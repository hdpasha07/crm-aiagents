# AI Customer Support Agent

An AI-assisted customer support application that classifies and prioritizes complaints, drafts responses, and gives support staff a dashboard for reviewing cases. The project combines a FastAPI backend, a LangGraph agent workflow, Gemini-powered retrieval over policy documents, and two React interfaces.

## What it does

- Accepts customer complaints through a REST API and customer-facing web app.
- Runs complaint conversations through a stateful LangGraph agent with tools for policy lookup, customer profiles, and prior resolutions.
- Uses Gemini and ChromaDB for retrieval-augmented responses grounded in local policy documents.
- Applies PII redaction and prompt-injection checks in the agent security components.
- Provides an employee dashboard with complaint status, priority, and analytics views.
- Stores complaint and customer state locally in SQLite; ChromaDB persistence is local as well.

Email notifications are currently printed as drafts to the backend console. The project does not send email through an SMTP service.

## Architecture

```text
Customer portal ─┐
                 ├─> FastAPI ─> complaint database
Employee dashboard┘       │
                           └─> LangGraph agent
                                ├─ Gemini model and tools
                                ├─ policy retrieval (ChromaDB)
                                └─ PII and injection guardrails
```

Main directories:

- `Agent/` — LangGraph workflow, agent tools, security components, and policy RAG.
- `Backend/` — FastAPI routes, SQLAlchemy models, CRUD operations, and worker.
- `Frontend/customer/` — Customer-facing React app.
- `Frontend/employee-dashboard/` — Employee complaint and analytics dashboard.
- `Email/` — Console-only email draft helper.
- `FinalisingAgent/` — Resolution schemas and logic.

## Requirements

- Python 3.10 or later
- Node.js 18 or later and npm
- A Google Gemini API key for model and embedding calls
- For PII recognition, install the spaCy English model after Python dependencies (command below)

## Run locally

1. Clone the repository and install backend dependencies:

   ```bash
   git clone <repository-url>
   cd Customer-Support-Agent
   python -m venv .venv
   # Windows PowerShell: .venv\Scripts\Activate.ps1
   # macOS/Linux: source .venv/bin/activate
   python -m pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

2. Create local configuration and add your own Gemini key:

   ```bash
   # Windows PowerShell
   Copy-Item .env.example .env
   # macOS/Linux
   cp .env.example .env
   ```

   Edit `.env` and set `GEMINI_API_KEY`. The `.env` file is ignored by Git.

3. Index the policy documents into the local ChromaDB store:

   ```bash
   python -m Agent.rag.ingest
   ```

4. Start the API:

   ```bash
   uvicorn main_api:app --reload
   ```

   The API is available at `http://localhost:8000`; interactive docs are at `http://localhost:8000/docs`.

5. In separate terminals, start either or both frontends:

   ```bash
   cd Frontend/customer
   npm ci
   npm run dev
   ```

   ```bash
   cd Frontend/employee-dashboard
   npm ci
   npm run dev
   ```

   Both frontends currently use `http://localhost:8000` as their API URL.

See [SETUP.md](SETUP.md) for additional setup details and the optional background worker.

## API overview

- `POST /complaints` — submit a complaint
- `GET /complaints` and `GET /complaints/{complaint_id}` — list and retrieve complaints
- `PATCH /complaints/{complaint_id}` and `DELETE /complaints/{complaint_id}` — update or delete a complaint
- `GET /complaints/by-email/{email}` — list complaints by customer email
- `GET /analytics/summary`, `/analytics/status`, `/analytics/priority`, `/analytics/trends` — dashboard metrics

## Configuration

See [`.env.example`](.env.example) for supported local settings. Never commit `.env`, API keys, customer records, SQLite databases, ChromaDB data, or logs.

## License

No license has been selected for this repository yet. Unless a license is added, standard copyright applies and reuse is not granted.
