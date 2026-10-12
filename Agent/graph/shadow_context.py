"""
Shadow Context Injector Interceptor
==================================
Pre-routing interceptor that dynamically queries the persistent customer profile
database and injects ONLY query-relevant profile attributes (e.g. recent orders,
tier, current shipping address) into the system prompt context.

Prevents context bloat and token waste by omitting irrelevant profile data on
generic policy or FAQ queries.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .database import get_db, CustomerProfileDB


class ShadowContextInjector:
    """Pre-routing context optimization interceptor."""

    def __init__(self, db: Optional[CustomerProfileDB] = None):
        self.db = db or get_db()

    # Keyword sets for targeted attribute extraction
    ORDER_KEYWORDS = {
        "order", "orders", "ord", "tracking", "track", "package", "shipment",
        "delivery", "delivered", "transit", "carrier", "item", "items", "bought",
        "purchased", "purchase", "shipped"
    }

    ADDRESS_KEYWORDS = {
        "address", "shipping", "deliver to", "ship to", "move", "moved",
        "relocate", "relocated", "street", "apartment", "apt", "city", "zip",
        "residence", "location", "destination"
    }

    TIER_KEYWORDS = {
        "tier", "vip", "gold", "platinum", "silver", "standard", "loyalty",
        "perk", "perks", "benefit", "benefits", "points", "membership", "rewards"
    }

    IDENTITY_KEYWORDS = {
        "account", "profile", "identity", "who am i", "my name", "my email",
        "my details", "registered", "info"
    }

    PREFERENCE_KEYWORDS = {
        "prefer", "preference", "preferences", "style", "format", "bullet",
        "concise", "detailed", "remember", "tone", "instructions"
    }

    def _matches_any(self, text: str, keywords: set[str]) -> bool:
        tokens = set(re.findall(r"\b[a-zA-Z0-9_\-']+\b", text.lower()))
        return bool(tokens & keywords)

    def extract_relevant_context(
        self,
        customer_id: str,
        query: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Extract only attributes relevant to the current user query.
        Returns a dict of relevant snippets, or None if no user data is relevant.
        """
        profile = self.db.get_profile(customer_id)
        if not profile:
            return None

        relevant: Dict[str, Any] = {}
        query_clean = query.lower()

        # 1. Order relevance check
        if self._matches_any(query_clean, self.ORDER_KEYWORDS):
            orders = profile.get("order_history", [])
            if orders:
                recent_orders = orders[:2]
                relevant["recent_orders"] = [
                    {
                        "order_id": o.get("order_id"),
                        "status": o.get("status"),
                        "carrier": o.get("carrier"),
                        "tracking": o.get("tracking_number"),
                        "est_delivery": o.get("estimated_delivery"),
                        "items": o.get("items", []),
                    }
                    for o in recent_orders
                ]

        # 2. Address / Shipping relevance check
        if self._matches_any(query_clean, self.ADDRESS_KEYWORDS):
            relevant["current_shipping_address"] = profile.get("current_shipping_address")

        # 3. Tier / Loyalty relevance check
        if self._matches_any(query_clean, self.TIER_KEYWORDS):
            relevant["tier"] = profile.get("tier")

        # 4. Identity / Account relevance check
        if self._matches_any(query_clean, self.IDENTITY_KEYWORDS):
            relevant["customer_name"] = profile.get("name")
            relevant["email"] = profile.get("email")

        # 5. Learned Preferences relevance check
        if self._matches_any(query_clean, self.PREFERENCE_KEYWORDS):
            prefs = profile.get("learned_preferences", {})
            pref_list = prefs.get("preferences", []) if isinstance(prefs, dict) else []
            if pref_list:
                relevant["learned_preferences"] = [p.get("preference") for p in pref_list if "preference" in p]

        # If nothing specifically matched, return None (generic query -> zero tokens wasted)
        if not relevant:
            return None

        relevant["customer_id"] = customer_id
        relevant["name"] = profile.get("name")
        return relevant

    def build_shadow_system_prompt(
        self,
        customer_id: str,
        query: str,
    ) -> Optional[str]:
        """
        Construct a concise, token-optimized shadow context string for system injection.
        """
        context = self.extract_relevant_context(customer_id, query)
        if not context:
            return None

        lines = [
            f"[SHADOW CONTEXT - SESSION RELEVANT USER DATA]",
            f"Active Customer: {context['name']} (ID: {context['customer_id']})",
        ]

        if "current_shipping_address" in context:
            lines.append(f"- Current Shipping Address: {context['current_shipping_address']}")

        if "tier" in context:
            lines.append(f"- Loyalty Tier: {context['tier']}")

        if "recent_orders" in context:
            lines.append("- Recent Orders:")
            for ord_data in context["recent_orders"]:
                lines.append(
                    f"  * {ord_data['order_id']} | Status: {ord_data['status']} | "
                    f"Carrier: {ord_data['carrier']} ({ord_data['tracking']}) | "
                    f"Items: {', '.join(ord_data.get('items', []))}"
                )

        if "email" in context:
            lines.append(f"- Email: {context['email']}")

        if "learned_preferences" in context:
            lines.append("- Learned User Preferences:")
            for p in context["learned_preferences"]:
                lines.append(f"  * {p}")

        lines.append("(Note: Non-relevant customer profile details omitted to optimize context window)")
        return "\n".join(lines)


# Singleton instance
_shadow_injector: Optional[ShadowContextInjector] = None


def get_shadow_injector() -> ShadowContextInjector:
    global _shadow_injector
    if _shadow_injector is None:
        _shadow_injector = ShadowContextInjector()
    return _shadow_injector
