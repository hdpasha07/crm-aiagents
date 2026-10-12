# Local setup

## Prerequisites

- Python 3.10 or later
- Node.js 18 or later and npm
- A Google Gemini API key

## Backend

From the repository root, create and activate a virtual environment, then install the Python dependencies:

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Copy `.env.example` to `.env` and set `GEMINI_API_KEY` to your own key. `.env` is ignored by Git. The default SQLite database and ChromaDB files are created locally and are not source files.

Index the included policy documents:

```bash
python -m Agent.rag.ingest
```

Run the API:

```bash
uvicorn main_api:app --reload
```

Open `http://localhost:8000/docs` for the interactive API documentation. The optional complaint worker can be run in another terminal with `python main_worker.py`.

## Frontend

Run each dashboard in a separate terminal:

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

Both frontends currently call the API at `http://localhost:8000`.

## Tests

Install the backend requirements, then run the test suite from the repository root with:

```bash
python -m pytest
```

Some integration and agent tests may require extra local services, a Gemini key, or preinstalled spaCy models. Email delivery is not configured; the current helper prints draft messages to the console.
