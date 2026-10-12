"""
AI Customer Support Agent Integration & Unit Test Suite
======================================================
Tests:
1. Middleware Guardrails: Microsoft Presidio PII scrubbing on incoming JSON payloads.
2. LangGraph Handoffs: Categorizer state update and routing to policy_agent or escalation.
3. ChromaDB Retrieval: Semantic search retrieving chunks from markdown policy documents.
"""

from __future__ import annotations

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from main_api import app
from Backend.db import SessionLocal
from Backend.crud import get_complaint_by_id
from Agent.graph_legacy import (
    categorize_node,
    policy_node,
    route_after_categorize,
    build_graph,
)
from Agent.schemas.category import CategoryOutput
from Agent.rag.vector_store import VectorStoreManager
from Agent.rag.document_loader import load_and_chunk_file


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient fixture."""
    return TestClient(app)


# ── 1. Middleware Guardrails (Microsoft Presidio) ──────────────────────────────

class TestMiddlewareGuardrails:
    """Verifies that Microsoft Presidio scrubs PII before payloads reach the graph/DB."""

    def test_presidio_scrubs_credit_card_and_ssn_from_payload(self, client: TestClient):
        payload = {
            "email": "customer@example.com",
            "order_id": "ORD-55412",
            "complaint_text": (
                "Unauthorized charge! My credit card is 4532-1122-3344-5566 and my SSN "
                "is 123-45-6789. Please issue a refund immediately."
            ),
        }

        response = client.post("/complaints", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "complaint_id" in data
        complaint_id = data["complaint_id"]

        # Verify the record persisted in the database has been scrubbed of raw PII
        db = SessionLocal()
        try:
            complaint = get_complaint_by_id(db, complaint_id)
            assert complaint is not None

            # Assert raw sensitive numbers are NOT present
            assert "4532-1122-3344-5566" not in complaint.complaint_text
            assert "123-45-6789" not in complaint.complaint_text

            # Assert anonymized placeholder tokens were injected
            assert "<CREDIT_CARD>" in complaint.complaint_text
            assert "<US_SSN>" in complaint.complaint_text
        finally:
            db.close()

    def test_presidio_scrubs_phone_number_from_payload(self, client: TestClient):
        payload = {
            "email": "sarah.smith@example.com",
            "order_id": "ORD-99120",
            "complaint_text": "Package never arrived. Call me back at 555-839-2019 right away.",
        }

        response = client.post("/complaints", json=payload)
        assert response.status_code == 200
        complaint_id = response.json()["complaint_id"]

        db = SessionLocal()
        try:
            complaint = get_complaint_by_id(db, complaint_id)
            assert complaint is not None
            assert "555-839-2019" not in complaint.complaint_text
            assert "<PHONE_NUMBER>" in complaint.complaint_text
        finally:
            db.close()


# ── 2. LangGraph Handoffs & Routing Logic ─────────────────────────────────────

class TestLangGraphHandoffs:
    """Verifies categorizer state updates and routing to policy_agent or escalation."""

    def test_categorizer_updates_state_and_routes_to_policy_agent(self, mocker):
        # Mock the categorizer LLM function to return a general delivery category
        mocker.patch(
            "Agent.graph_legacy.categorize",
            return_value=CategoryOutput(category="delivery_issue"),
        )

        initial_state = {
            "complaint_text": "Where is my package? The tracking has not updated.",
            "is_valid": True,
        }

        # 1. Verify categorizer node updates the state dictionary
        updated_state = categorize_node(initial_state)
        assert updated_state["category"] == "delivery_issue"

        # 2. Verify routing logic directs to policy_agent
        next_node = route_after_categorize(updated_state)
        assert next_node == "policy_agent", f"Expected 'policy_agent', got '{next_node}'"

    def test_categorizer_updates_state_and_routes_to_escalation(self, mocker):
        # Mock the categorizer LLM function to return an urgent payment issue
        mocker.patch(
            "Agent.graph_legacy.categorize",
            return_value=CategoryOutput(category="payment_issue"),
        )

        initial_state = {
            "complaint_text": "I was double charged on my credit card for order ORD-123.",
            "is_valid": True,
        }

        # 1. Verify categorizer node updates the state dictionary
        updated_state = categorize_node(initial_state)
        assert updated_state["category"] == "payment_issue"

        # 2. Verify routing logic directs to escalation
        next_node = route_after_categorize(updated_state)
        assert next_node == "escalation", f"Expected 'escalation', got '{next_node}'"

    def test_policy_node_execution_updates_handled_by(self):
        state = {"complaint_text": "Need return policy details", "category": "feedback"}
        res = policy_node(state)
        assert res.get("handled_by") == "policy_agent"


# ── 3. ChromaDB Retrieval & Vector Store ──────────────────────────────────────

class TestChromaDBRetrieval:
    """Verifies vector store indexing and chunk retrieval from markdown policy documents."""

    @pytest.fixture(autouse=True)
    def setup_vector_store(self):
        self.vsm = VectorStoreManager()
        # Ingest policies directory if store is empty
        policies_dir = Path("Agent/policies").resolve()
        if self.vsm.count() == 0 and policies_dir.exists():
            self.vsm.ingest_directory(policies_dir)

    def test_retrieves_chunks_from_refund_policy_markdown(self):
        query = "What is the return window and refund eligibility timeline?"
        chunks = self.vsm.similarity_search(query=query, top_k=3)

        assert len(chunks) > 0, "No chunks retrieved from ChromaDB vector store!"
        top_chunk = chunks[0]

        # Verify content, metadata, and relevance score
        assert top_chunk.content, "Chunk content must not be empty"
        assert top_chunk.relevance_score is not None
        assert top_chunk.relevance_score > 0.0

        # Verify the source document points to a markdown policy
        source = top_chunk.metadata.get("source", "")
        assert "policy" in source.lower() or "refund" in source.lower() or source.endswith(".md")

        # Verify substantive policy details are retrieved
        all_text = " ".join([c.content.lower() for c in chunks])
        assert "refund" in all_text or "return" in all_text or "14" in all_text

    def test_retrieves_chunks_from_shipping_policy_markdown(self):
        query = "How long does standard ground shipping take and what carriers are used?"
        chunks = self.vsm.similarity_search(query=query, top_k=3)

        assert len(chunks) > 0, "No chunks retrieved for shipping inquiry!"
        all_text = " ".join([c.content.lower() for c in chunks])
        assert "shipping" in all_text or "delivery" in all_text or "carrier" in all_text

