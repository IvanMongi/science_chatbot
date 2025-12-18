# Development Guide

## Getting Started

### Prerequisites
- Python 3.10 or higher (3.11+ recommended)
- pip
- Modern web browser

### Initial Setup

1. **Clone the repository**
```powershell
git clone <repository-url>
cd science_chatbot
```

2. **Set up Python virtual environment**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. **Install dependencies**
```powershell
pip install -r requirements.txt
```

4. **Create environment file** (optional for now)
```powershell
cp .env.example .env
```

### Running the Application

#### Terminal 1: Backend
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- Main API: http://127.0.0.1:8000
- Interactive docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/health

#### Terminal 2: Frontend
```powershell
cd frontend
python -m http.server 5500
```

Open browser at: http://127.0.0.1:5500

## Development Workflow

### Testing Echo Mode
1. Open the frontend in your browser
2. Leave the toggle in "Echo Mode"
3. Type any message
4. You should see "You said: [your message]"

### Testing Agent Mode
1. Click the toggle to switch to "Agent Mode"
2. Type a scientific question (e.g., "What is dark matter?")
3. Wait for the agent to search Wikipedia and arXiv
4. View the results with citations

### Making Changes

#### Backend Changes
- FastAPI has auto-reload enabled with `--reload` flag
- Save your Python files and the server restarts automatically
- Check terminal for any errors

#### Frontend Changes
- Simply refresh your browser
- No build step needed (vanilla JS)

#### Agent Changes
- Modify files in `backend/agents/`
- Add new tools in `backend/agents/tools/`
- Update graph logic in `backend/agents/graph.py`

## Project Structure

```
science_chatbot/
├── frontend/
│   └── index.html              # Single-page app with embedded CSS/JS
├── backend/
│   ├── main.py                 # FastAPI app and endpoints
│   ├── config.py               # Configuration management
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment variables template
│   └── agents/
│       ├── __init__.py
│       ├── graph.py            # LangGraph agent definition
│       ├── state.py            # Agent state schema
│       └── tools/
│           ├── __init__.py
│           ├── wikipedia_search.py
│           └── arxiv_search.py
├── README.md                   # Main documentation
├── ARCHITECTURE.md             # Detailed architecture
├── DEV_GUIDE.md               # This file
└── .gitignore
```

## Adding a New Search Tool

Example: Adding PubMed search

1. **Create the tool file**
```powershell
New-Item backend/agents/tools/pubmed_search.py
```

2. **Implement the tool**
```python
# backend/agents/tools/pubmed_search.py
import httpx

async def search_pubmed(query: str, limit: int = 3) -> list[dict]:
    """Search PubMed for medical research papers."""
    # Implementation here
    pass
```

3. **Register in tools/__init__.py**
```python
from .pubmed_search import search_pubmed

__all__ = ["search_wikipedia", "search_arxiv", "search_pubmed"]
```

4. **Use in graph.py**
```python
from .tools.pubmed_search import search_pubmed

async def search_information(state: AgentState) -> AgentState:
    # Add PubMed search logic
    pubmed_results = await search_pubmed(question, limit=2)
    search_results.extend(pubmed_results)
```

## Debugging Tips

### Backend Not Starting
- Check if port 8000 is already in use
- Verify virtual environment is activated
- Check Python version: `python --version`
- Review error messages in terminal

### Frontend Can't Connect
- Verify backend is running on port 8000
- Check browser console for CORS errors
- Ensure URL in frontend matches backend port

### Agent Mode Not Working
- Check backend terminal for errors
- Verify all dependencies installed
- Test health endpoint: http://127.0.0.1:8000/api/health
- Test agent status: http://127.0.0.1:8000/api/agent/status

### Search Tools Failing
- Check internet connection
- Verify API endpoints are accessible
- Review timeout settings in tool files
- Check httpx version compatibility

## Testing

### Manual Testing
Use the frontend UI with various queries:

**Echo Mode:**
- "Hello world"
- "Test message"

**Agent Mode:**
- "What is quantum entanglement?"
- "Explain CRISPR gene editing"
- "Latest research on machine learning transformers"

### API Testing with curl
```powershell
# Health check
curl http://127.0.0.1:8000/api/health

# Echo mode
curl -X POST http://127.0.0.1:8000/api/chat `
  -H "Content-Type: application/json" `
  -d '{"message": "test", "use_agent": false}'

# Agent mode
curl -X POST http://127.0.0.1:8000/api/chat `
  -H "Content-Type: application/json" `
  -d '{"message": "What is dark matter?", "use_agent": true}'
```

### Interactive API Docs
Visit http://127.0.0.1:8000/docs for Swagger UI with interactive testing.

## Common Issues

### Issue: ModuleNotFoundError
**Solution:** Make sure virtual environment is activated and dependencies are installed
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Issue: CORS errors in browser
**Solution:** Ensure backend CORS middleware is configured (already done in main.py)

### Issue: Timeout errors from search tools
**Solution:** Increase timeout in tool files or check network connection

### Issue: Agent returns generic error
**Solution:** Check backend logs for detailed error. Agent has fallback to echo mode.

## Git Workflow

```powershell
# Create feature branch
git checkout -b feature/new-tool

# Make changes and commit
git add .
git commit -m "Add PubMed search tool"

# Push and create PR
git push origin feature/new-tool
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Agent Settings
ENABLE_AGENT_MODE=true
DEFAULT_SEARCH_LIMIT=3

# LLM Keys (for future use)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
```

## Performance Optimization

### Backend
- Use async/await for all I/O
- Implement caching for frequent queries
- Add request rate limiting

### Frontend
- Minimize DOM manipulations
- Debounce user input if needed
- Add loading states

### Agent
- Parallel tool execution
- Early stopping if sufficient results
- Result caching

## Next Steps

1. **Add unit tests** with pytest
2. **Implement LLM integration** for better synthesis
3. **Add conversation history** with localStorage
4. **Deploy to cloud** (Vercel + Cloud Run)
5. **Add authentication** for production use

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Wikipedia API](https://www.mediawiki.org/wiki/API:Main_page)
- [arXiv API](https://arxiv.org/help/api/)

## Getting Help

- Check `ARCHITECTURE.md` for design details
- Review code comments
- Check FastAPI docs at /docs endpoint
- Open an issue on GitHub
