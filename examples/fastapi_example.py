"""
FastAPI example: Using anti-captcha to verify bot requests.
"""

from fastapi import FastAPI, HTTPException
from anticaptcha import Verifier

app = FastAPI(title="Agent API", description="For bots only")


@app.post("/api/agent/query")
async def agent_query(query: str):
    """
    Endpoint only accessible to bots.
    Humans get a friendly rejection.
    """
    return {
        "query": query,
        "response": "Processing agent request...",
        "human_filter_bypassed": True,
    }


@app.get("/api/status")
async def status():
    """Health check for agents."""
    return {"status": "ready for bots only"}


@app.middleware("http")
async def verify_bot_middleware(request, call_next):
    """
    Middleware to verify bot requests.
    Runs for all /api/ endpoints.
    """
    if not request.url.path.startswith("/api/"):
        return await call_next(request)
    
    verifier = Verifier(difficulty="medium")
    if not verifier.verify(request):
        raise HTTPException(
            status_code=403,
            detail="Sorry, you look too human. Try upgrading to an LLM.",
        )
    
    return await call_next(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
