# Science Chatbot

A ChatGPT-style interface for asking scientific questions with source citations. Built with FastAPI backend and vanilla JavaScript frontend, featuring LangGraph agents for intelligent information retrieval.

## 🎯 Features

- **Clean chat interface** inspired by modern AI assistants
- **LangGraph agents** with tools for scientific search and citation
- **Persistent conversations** - Chat history survives server restarts
- **Thread management** - Create, view, and delete conversation threads
- **RESTful API** built with FastAPI
- **Modular architecture** ready for portfolio showcase

## 📁 Project Structure

```
science_chatbot/
├── frontend/          # Static HTML/CSS/JS interface
│   └── index.html
├── backend/           # FastAPI server + LangGraph agents
│   ├── main.py        # API endpoints
│   ├── agents/        # LangGraph agent modules
│   └── requirements.txt
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+ (recommended 3.11+)
- Modern web browser

### Backend Setup (FastAPI + LangGraph)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API endpoints:
- Health check: `http://127.0.0.1:8000/api/health`
- Chat: `http://127.0.0.1:8000/api/chat`

### Frontend Setup

In a separate terminal:

```powershell
cd frontend
python -m http.server 5500
```

Open browser at `http://127.0.0.1:5500/`

> **Note:** Frontend expects backend at `http://127.0.0.1:8000/api/chat`. If you change the port, update the fetch URL in `frontend/index.html`.

## � Persistence & Database

The chatbot now features full conversation persistence using SQLite:

- **Messages survive server restarts** - All chat history is stored in `conversations.db`
- **Thread management** - Create, view, and delete conversation threads
- **Message history** - Click on any past conversation to load complete history
- **Automatic migration** - Database schema updates automatically on first run

### Testing Persistence

```powershell
cd backend
python test_message_persistence.py
```

See [MIGRATION_GUIDE.md](backend/MIGRATION_GUIDE.md) for detailed information about the persistence implementation.

## �🔄 Current Status

**Phase 1** (Completed):
- ✅ Frontend chat interface
- ✅ FastAPI backend skeleton
- ✅ Echo endpoint for testing

**Phase 2** (Completed):
- ✅ LangGraph agent architecture
- ✅ Scientific search tools (Wikipedia, arXiv)
- ✅ Conversation persistence with SQLite
- ✅ Thread management (create, list, delete)
- ✅ Message history across server restarts

**Phase 3** (In Progress):
- 🔨 Enhanced citation formatting
- 🔨 Advanced search strategies
- 🔨 Production deployment

## 🛠️ Tech Stack

- **Frontend:** Vanilla JavaScript, CSS3, HTML5
- **Backend:** FastAPI, LangGraph, Python 3.11+
- **Database:** SQLite for conversation persistence
- **AI/Agents:** LangGraph for agent orchestration
- **Tools:** Wikipedia API, arXiv API

## 📝 Usage Flow

1. User types a scientific question in the chat input
2. Frontend sends `{"message": "...", "thread_id": "..."}` to backend
3. Backend loads previous messages from database (if any)
4. LangGraph agent processes question with full context
5. Agent may call search tools (Wikipedia, arXiv) to gather information
6. Response with citations is generated
7. New messages are saved to database
8. Chat displays user message and bot response with sources

## 🎓 Portfolio Notes

This project demonstrates:
- Modern async Python with FastAPI
- Agent-based architecture with LangGraph
- Clean frontend-backend separation
- RESTful API design
- Modular code structure for scalability

## 📋 Roadmap

- [x] Integrate LangGraph agents with search tools
- [x] Add Wikipedia and arXiv search capabilities
- [x] Implement citation formatting
- [x] Add conversation history persistence
- [ ] Enhanced message search and filtering
- [ ] Conversation export functionality
- [ ] Unit tests with pytest
- [ ] Production deployment with Docker
- [ ] Docker containerization
