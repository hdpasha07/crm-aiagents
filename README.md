# Customer Support Agent

An intelligent, AI-powered customer support automation system built with LangChain and LangGraph. Automatically processes, categorizes, prioritizes, and responds to customer complaints with multi-agent workflow orchestration.

## Features

- **Intelligent Complaint Processing** - Automated validation, categorization, and sentiment analysis
- **Dynamic Priority Assignment** - Smart prioritization based on sentiment, category, and urgency
- **Automated Email Responses** - Context-aware response generation with policy compliance
- **Human Escalation** - Automatic escalation for high-priority cases requiring human intervention
- **Analytics Dashboard** - Real-time metrics, trends, and complaint tracking
- **Dual Frontend** - Customer complaint submission portal and employee management dashboard
- **RESTful API** - Complete CRUD operations with FastAPI backend
- **Persistent Storage** - SQLite database with SQLAlchemy ORM

## Architecture

The system uses a **multi-agent workflow** powered by LangGraph with the following pipeline:

```
Validation → Categorization → Sentiment Analysis → Priority Assignment 
    → Response Generation → Action Suggestions → Re-evaluation 
    → Escalation Decision → Human Review (if needed)
```

### Agent Pipeline

1. **Validation Agent** - Validates complaint legitimacy and completeness
2. **Categorization Agent** - Classifies complaints into predefined categories
3. **Sentiment Agent** - Analyzes emotional tone (positive, negative, neutral)
4. **Priority Agent** - Assigns priority levels (low, medium, high, critical)
5. **Response Agent** - Generates appropriate email responses
6. **Suggestion Agent** - Recommends actionable steps for resolution
7. **Re-evaluation Agent** - Reviews priority based on context
8. **Escalation Agent** - Determines if human intervention is required

## Tech Stack

**Backend:**
- Python 3.x
- FastAPI - REST API framework
- LangChain - LLM orchestration
- LangGraph - Multi-agent workflow
- Groq - LLM provider
- SQLAlchemy - ORM
- SQLite - Database
- Pydantic - Data validation

**Frontend:**
- React - Customer portal
- React - Employee dashboard
- Axios - HTTP client

## Project Structure

```
Customer-Support-Agent/
├── Agent/
│   ├── agents/          # Individual agent implementations
│   ├── memory/          # Conversation memory management
│   ├── policies/        # Business rules and policies
│   ├── schemas/         # Pydantic models
│   ├── utils/           # Helper utilities
│   ├── graph.py         # LangGraph workflow definition
│   ├── state.py         # State management
│   └── main.py          # Agent entry point
├── Backend/
│   ├── api.py           # FastAPI routes
│   ├── crud.py          # Database operations
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── worker.py        # Background worker
│   └── db.py            # Database configuration
├── Frontend/
│   ├── customer/        # Customer complaint portal
│   └── employee-dashboard/  # Staff management interface
├── Email/               # Email notification system
└── FinalisingAgent/     # Final processing logic
```

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend)
- Groq API key

### Installation

1. Clone the repository
```bash
git clone https://github.com/MasirJafri1/Customer-Support-Agent.git
cd Customer-Support-Agent
```

2. Install Python dependencies
```bash
pip install -r requirements.txt
```

3. Configure environment variables

Create a `.env` file:
```env
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=sqlite:///./complaints.db
```

4. Initialize the database
```bash
python seed_data.py
```

5. Start the FastAPI backend
```bash
python main_api.py
# or
uvicorn Backend.api:app --reload
```

6. Start the background worker
```bash
python main_worker.py
```

7. Start the frontend (in separate terminals)
```bash
# Customer portal
cd Frontend/customer
npm install
npm run dev

# Employee dashboard
cd Frontend/employee-dashboard
npm install
npm run dev
```

## API Endpoints

### Complaints

- `POST /complaints` - Submit a new complaint
- `GET /complaints` - List all complaints (with optional filters)
- `GET /complaints/{id}` - Get complaint by ID
- `PATCH /complaints/{id}` - Update complaint status/priority
- `DELETE /complaints/{id}` - Delete a complaint
- `GET /complaints/by-email/{email}` - Get complaints for a customer

### Analytics

- `GET /analytics/summary` - Overall metrics summary
- `GET /analytics/status` - Breakdown by status
- `GET /analytics/priority` - Breakdown by priority
- `GET /analytics/trends` - Daily complaint trends

## Usage

### Customer Flow
1. Visit the customer portal
2. Enter email, order ID, and complaint details
3. System automatically processes and responds
4. Receive automated email response

### Employee Flow
1. Access employee dashboard
2. View all complaints with filters
3. Monitor real-time analytics
4. Handle escalated cases requiring human review

## Key Features Explained

### Intelligent Categorization
Complaints are automatically classified into categories like:
- Product Quality
- Shipping Issues
- Customer Service
- Billing Problems
- Technical Issues

### Priority System
- **Low** - Minor issues, no immediate action needed
- **Medium** - Moderate concerns, standard resolution timeline
- **High** - Significant issues requiring prompt attention
- **Critical** - Urgent matters with potential escalation

### Automated Responses
AI-generated responses are:
- Contextually relevant
- Policy-compliant
- Empathetic and professional
- Actionable with clear next steps

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Author

**Masir Jafri**

- Website: [masirjafri.in](https://www.masirjafri.in)
- GitHub: [@MasirJafri1](https://github.com/MasirJafri1)
- LinkedIn: [masirjafri](https://www.linkedin.com/in/masirjafri)

## Acknowledgments

- Built with [LangChain](https://langchain.com/) and [LangGraph](https://langchain-ai.github.io/langgraph/)
- Powered by [Groq](https://groq.com/)
- API framework: [FastAPI](https://fastapi.tiangolo.com/)

---
