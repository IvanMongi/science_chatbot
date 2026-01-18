# Quick Start Guide - Testing Persistence

## Prerequisites
- Python 3.10+
- Backend dependencies installed (`pip install -r requirements.txt`)

## Setup (First Time Only)

```bash
# Navigate to project root
cd science_chatbot

# Install dependencies
cd backend
pip install -r requirements.txt
cd ..
```

## Testing Persistence Layer

```bash
# Test backend persistence module
cd backend
python test_persistence.py

# Expected output:
# ✓ Checkpointer initialized successfully
# ✓ Checkpointer is singleton
# ✓ Database table 'conversation_threads' created
# ✓ Database schema is correct
# ✓ Thread created successfully
# ✓ Single thread retrieved successfully
# ✓ Thread metadata updated successfully
# ✓ Threads list retrieved successfully
# ✓ Thread deleted successfully
# ✓ Pagination works correctly
# ✓ Threads ordered correctly (newest first)
# ✅ All tests passed!
```

## Running the Full Application

### Terminal 1 - Backend Server
```bash
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Terminal 2 - Frontend Server
```bash
cd frontend
python -m http.server 3000
```

Expected output:
```
Serving HTTP on 0.0.0.0 port 3000 (http://0.0.0.0:3000/) ...
```

### Open in Browser
Navigate to: **http://localhost:3000**

## Testing Features

### 1. Create New Chat
- Click "+ New Chat" button in sidebar
- Chat area should clear
- Write a message and click Send

### 2. View Thread History
- After sending a message, check the sidebar
- New thread should appear with title and preview
- Threads should be sorted by most recent first

### 3. Switch Between Threads
- Click on any thread in the sidebar
- Chat content should update
- Thread should be highlighted in sidebar

### 4. Delete Thread
- Click the ✕ button on any thread
- Confirm deletion when prompted
- Thread should disappear from sidebar

### 5. Check API Documentation
- Visit: **http://localhost:8000/docs**
- Scroll down to see all endpoints
- Try out GET /api/threads to see your saved threads

## Files Location

```
science_chatbot/
├── backend/
│   ├── persistence.py          ✨ NEW - Persistence layer
│   ├── main.py                 📝 MODIFIED - Enhanced API
│   ├── test_persistence.py     ✨ NEW - Test suite
│   ├── agents/
│   │   └── graph.py            📝 MODIFIED - With checkpointer
│   └── requirements.txt
├── frontend/
│   ├── index.html              📝 MODIFIED - Sidebar layout
│   ├── styles.css              📝 MODIFIED - Sidebar styling
│   └── script.js               📝 MODIFIED - Thread management
├── PERSISTENCE_COMPLETE.md     ✨ NEW - Full documentation
└── README.md
```

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
# Try a different port:
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

### Frontend won't load
```bash
# Check if port 3000 is in use
# Try a different port:
python -m http.server 3001
# Then visit http://localhost:3001
```

### Tests fail
```bash
# Make sure you're in the backend directory
cd backend

# Check Python version (needs 3.10+)
python --version

# Verify dependencies installed
pip list | grep -E "langgraph|pydantic|fastapi"
```

### Chat not working
1. Ensure both servers are running (check Terminal 1 & 2)
2. Check browser console (F12) for errors
3. Check that API URL in script.js matches your backend URL
4. Verify API is responding: `curl http://localhost:8000/api/health`

## Database

- **Location**: `backend/conversations.db`
- **Type**: SQLite
- **Auto-created**: Yes, on first run
- **To reset**: Delete `backend/conversations.db` and restart backend

## Key Endpoints to Test

```bash
# Health check
curl http://localhost:8000/api/health

# Get all threads
curl http://localhost:8000/api/threads

# Send a message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is photosynthesis?",
    "thread_id": null,
    "use_agent": true
  }'

# View API docs
open http://localhost:8000/docs
```

## Performance Notes

- First message to a new thread takes ~2-5 seconds (agent initialization)
- Subsequent messages are faster (~500ms-2s)
- Thread switching is instant
- Sidebar updates after each message

---

**Status**: Ready to test! 🚀
