# Science Chatbot - Architecture Documentation

## Overview

This project implements an intelligent scientific research assistant using LangGraph for agent orchestration, FastAPI for the backend API, and a clean vanilla JavaScript frontend.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  index.html (Vanilla JS + CSS)                       │   │
│  │  - Chat UI with mode toggle (Echo/Agent)             │   │
│  │  - Real-time message rendering                       │   │
│  │  - Example prompts                                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                         HTTP/JSON
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Backend API Layer                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  FastAPI (main.py)                                   │   │
│  │  - /api/chat         → Process user messages         │   │
│  │  - /api/health       → Health check                  │   │
│  │  - /api/agent/status → Agent availability            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │
┌─────────────────────────────────────────────────────────────┐
│                     LangGraph Agent Layer                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  StateGraph (graph.py)                               │   │
│  │  ┌──────────────┐    ┌──────────────┐               │   │
│  │  │  Classify    │───▶│   Search     │               │   │
│  │  │  Question    │    │  Information │               │   │
│  │  └──────────────┘    └──────────────┘               │   │
│  │                             │                        │   │
│  │                             ▼                        │   │
│  │                      ┌──────────────┐                │   │
│  │                      │  Generate    │                │   │
│  │                      │  Answer      │                │   │
│  │                      └──────────────┘                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
┌─────────────────────────┐   ┌──────────────────────────┐
│    Wikipedia API        │   │      arXiv API           │
│  - General concepts     │   │  - Scientific papers     │
│  - Quick reference      │   │  - Research articles     │
└─────────────────────────┘   └──────────────────────────┘
```

## Component Breakdown

### 1. Frontend (`frontend/index.html`)

**Technology:** Vanilla JavaScript, HTML5, CSS3

**Key Features:**
- Clean, modern chat interface inspired by ChatGPT
- Mode toggle: Switch between Echo mode (testing) and Agent mode (LangGraph)
- Responsive design with custom CSS
- Real-time message rendering
- Example prompt suggestions

**Design Decisions:**
- No framework dependencies → Fast load times, easy deployment
- Custom CSS with CSS variables → Easy theming
- Async/await for API calls → Clean, modern JS

### 2. API Layer (`backend/main.py`)

**Technology:** FastAPI, Pydantic

**Endpoints:**
- `POST /api/chat`: Main chat endpoint with mode selection
  - `use_agent=false`: Echo mode (returns "You said: {message}")
  - `use_agent=true`: Agent mode (uses LangGraph)
- `GET /api/health`: System health check
- `GET /api/agent/status`: Check agent availability

**Features:**
- CORS enabled for frontend-backend communication
- Request/response validation with Pydantic
- Error handling with graceful fallback
- Type-safe async handlers

### 3. LangGraph Agent System (`backend/agents/`)

**Architecture:** State-based graph with three nodes

#### State Definition (`state.py`)
```python
AgentState:
  - messages: Conversation history
  - question: Original user query
  - search_results: Results from tools
  - final_answer: Formatted response with citations
```

#### Graph Flow (`graph.py`)

1. **Classify Node**
   - Analyzes question keywords
   - Determines search strategy:
     - "general": Wikipedia focus
     - "papers": Wikipedia + arXiv

2. **Search Node**
   - Executes parallel searches based on strategy
   - Aggregates results from multiple sources
   - Handles API errors gracefully

3. **Generate Node**
   - Synthesizes information from search results
   - Formats answer with proper citations
   - Returns structured response

#### Tools (`agents/tools/`)

**Wikipedia Search** (`wikipedia_search.py`)
- Searches Wikipedia API
- Returns: title, snippet, URL
- Async and sync implementations
- Error handling with fallback

**arXiv Search** (`arxiv_search.py`)
- Searches arXiv API for scientific papers
- XML parsing for paper metadata
- Returns: title, authors, abstract, URL
- Relevance-based sorting

### 4. Configuration (`backend/config.py`)

**Technology:** Pydantic Settings

**Features:**
- Environment variable loading from `.env`
- Type-safe configuration
- Default values for all settings
- Ready for API key integration (OpenAI, Anthropic)

## Data Flow

### Echo Mode Flow
```
User Input → Frontend → FastAPI → Echo Response → Frontend → Display
```

### Agent Mode Flow
```
User Input → Frontend → FastAPI → LangGraph Agent
                                      ↓
                              Classify Question
                                      ↓
                              Search Wikipedia + arXiv
                                      ↓
                              Generate Answer with Citations
                                      ↓
                             Frontend ← Response
```

## Technology Stack

| Layer           | Technology        | Purpose                           |
|-----------------|-------------------|-----------------------------------|
| Frontend        | Vanilla JS        | UI/UX, user interaction          |
| API             | FastAPI           | RESTful API, request handling    |
| Agent Framework | LangGraph         | Agent orchestration, state mgmt  |
| HTTP Client     | httpx             | Async external API calls         |
| Validation      | Pydantic          | Data validation, settings        |
| Server          | Uvicorn           | ASGI server                      |

## Design Patterns

1. **State Graph Pattern (LangGraph)**
   - Explicit state transitions
   - Testable nodes
   - Easy to visualize and debug

2. **Repository Pattern (Tools)**
   - Each tool is independent
   - Easy to add new sources
   - Async by default

3. **Dependency Injection**
   - Settings via environment
   - Configurable without code changes

4. **Error Handling Strategy**
   - Graceful degradation
   - Fallback to echo mode on agent errors
   - User-friendly error messages

## Future Enhancements

### Phase 2 (Short-term)
- [ ] Integrate LLM (OpenAI/Anthropic) for intelligent synthesis
- [ ] Add semantic search for more relevant results
- [ ] Implement conversation history
- [ ] Add more tools (PubMed, Google Scholar)

### Phase 3 (Mid-term)
- [ ] Streaming responses for better UX
- [ ] Multi-turn conversations with context
- [ ] User authentication and saved chats
- [ ] Rate limiting and caching

### Phase 4 (Long-term)
- [ ] Vector database for document retrieval
- [ ] Fine-tuned models for scientific domain
- [ ] Citation verification system
- [ ] PDF paper parsing and analysis

## Development Guidelines

### Adding a New Tool

1. Create tool file in `backend/agents/tools/`
2. Implement async function with standard return format
3. Add tool to `__init__.py`
4. Update graph to use new tool
5. Add unit tests

### Adding a New Graph Node

1. Define node function in `graph.py`
2. Update `AgentState` if needed
3. Add node to workflow: `workflow.add_node()`
4. Define edges: `workflow.add_edge()`
5. Test with example queries

### Environment Setup

```powershell
# Backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Frontend (separate terminal)
cd frontend
python -m http.server 5500
```

## Testing Strategy

### Unit Tests (TODO)
- Test each tool independently
- Test graph nodes with mock state
- Test API endpoints with TestClient

### Integration Tests (TODO)
- End-to-end flow with real APIs
- Error scenarios
- Performance benchmarks

### Manual Testing
- Use echo mode to verify connectivity
- Toggle to agent mode for LangGraph testing
- Try example prompts

## Performance Considerations

- **Async/await**: All I/O operations are async
- **Parallel searches**: Wikipedia and arXiv searched simultaneously
- **Request timeout**: 10-15s to prevent hanging
- **Connection pooling**: httpx reuses connections

## Security Notes

- CORS currently set to `*` (development only)
- No authentication (add for production)
- API keys stored in `.env` (never commit)
- Input validation via Pydantic

## Deployment Considerations

### Development
- Frontend: `python -m http.server`
- Backend: `uvicorn main:app --reload`

### Production (Future)
- Frontend: Static hosting (Vercel, Netlify)
- Backend: Docker container on Cloud Run / AWS ECS
- Environment: `.env` via secrets manager
- Monitoring: Logging, error tracking

## Portfolio Highlights

This project demonstrates:
- ✅ Modern Python async patterns
- ✅ LangGraph agent architecture
- ✅ RESTful API design with FastAPI
- ✅ Clean frontend-backend separation
- ✅ Modular, testable code structure
- ✅ Type safety throughout
- ✅ Real-world tool integration
- ✅ Graceful error handling
- ✅ Documentation and architecture design
