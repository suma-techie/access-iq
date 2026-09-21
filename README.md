# AccessIQ

AccessIQ is an access-request/approval system. Instead of a person filing a ticket and hoping the
right approver notices it, an agent grounds every request in real evidence — an assigned task,
an uploaded document, or an exact permission-catalog match — before proposing anything. A routing engine then decides what happens next: auto-approve, route to the right human
approver, or escalate, based on severity and how confidently the request was grounded.

**Live demo:** https://brave-sky-0e4c47b0f-preview.eastus2.6.azurestaticapps.net

## Features

- Conversational, chat-based access requests instead of static forms
- Evidence-backed grounding (tasks, documents, permission catalog) before any request is proposed
- Role-based approval queues for team leads, application owners, and managers
- Delegation support so approvals keep flowing when an approver is unavailable
- Full audit trail for every request, decision, and revocation

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python), SQLAlchemy, Alembic |
| Frontend | React, TypeScript, Vite |
| Database | PostgreSQL |

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # fill in your database and API credentials
alembic upgrade head
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env      # point this at your backend URL
npm run dev
```

The app will be available at `http://localhost:5173`.

## Project Structure

```
AccessIQ/
├── backend/    # FastAPI application, database models, migrations
└── frontend/   # React single-page application
```

## License

This project is currently unlicensed / proprietary.
