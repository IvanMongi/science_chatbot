# Science Chatbot

A ChatGPT-style interface for asking scientific questions with source citations. Built with FastAPI backend and vanilla JavaScript frontend, featuring LangGraph agents for intelligent information retrieval.

## 🎯 Features

- **Clean chat interface** inspired by modern AI assistants
- **LangGraph agents** with tools for scientific search and citation
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

## 🔄 Current Status

**Phase 1** (Completed):
- ✅ Frontend chat interface
- ✅ FastAPI backend skeleton
- ✅ Echo endpoint for testing

**Phase 2** (In Progress):
- 🔨 LangGraph agent architecture
- 🔨 Scientific search tools
- 🔨 Citation formatting

## 🛠️ Tech Stack

- **Frontend:** Vanilla JavaScript, CSS3, HTML5
- **Backend:** FastAPI, LangGraph, Python 3.11+
- **AI/Agents:** LangGraph for agent orchestration
- **Tools:** Wikipedia API, arXiv API (planned)

## 📝 Usage Flow

1. User types a scientific question in the chat input
2. Frontend sends `{"message": "..."}` to backend
3. Backend (currently) echoes: `{"reply": "You said: ..."}`
4. Chat displays user message and bot response

## 🎓 Portfolio Notes

This project demonstrates:
- Modern async Python with FastAPI
- Agent-based architecture with LangGraph
- Clean frontend-backend separation
- RESTful API design
- Modular code structure for scalability

## 📋 Roadmap

- [ ] Integrate LangGraph agents with search tools
- [ ] Add Wikipedia and arXiv search capabilities
- [ ] Implement citation formatting
- [ ] Add conversation history persistence
- [ ] Unit tests with pytest
- [ ] Docker containerization
