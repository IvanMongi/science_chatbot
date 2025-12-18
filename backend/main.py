from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents.graph import run_agent

app = FastAPI(
    title="Science Chatbot API",
    version="0.2.0",
    description="Scientific information retrieval chatbot with LangGraph agents"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    use_agent: bool = False  # Toggle between echo and agent mode


class ChatResponse(BaseModel):
    reply: str
    mode: str  # "echo" or "agent"


@app.get("/api/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "version": "0.2.0"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """
    Chat endpoint that can operate in two modes:
    - Echo mode (default): Returns "You said: {message}"
    - Agent mode: Uses LangGraph agent to search and answer with citations
    """
    if req.use_agent:
        try:
            answer = await run_agent(req.message)
            return ChatResponse(reply=answer, mode="agent")
        except Exception as e:
            error_msg = f"Agent error: {str(e)}. Falling back to echo mode."
            print(error_msg)
            return ChatResponse(reply=f"You said: {req.message}\n\n[{error_msg}]", mode="echo")
    else:
        # Echo mode
        echo = f"You said: {req.message}"
        return ChatResponse(reply=echo, mode="echo")


@app.get("/api/agent/status")
async def agent_status() -> dict:
    """Check if agent mode is available."""
    try:
        from agents.graph import create_science_agent
        agent = create_science_agent()
        return {
            "available": True,
            "message": "LangGraph agent is ready"
        }
    except Exception as e:
        return {
            "available": False,
            "message": f"Agent not available: {str(e)}"
        }


# To run: uvicorn main:app --reload --host 0.0.0.0 --port 8000
