"""
Demo: anti-captcha protecting a FastAPI server.

Run:
    cd examples && uvicorn demo_server:app --port 8000

Then try:
    # Without token (rejected)
    curl http://localhost:8000/api/hello
    
    # With bot client (auto-solves challenge)
    python demo_client.py
"""

from fastapi import FastAPI
from anticaptcha.server import AntiCaptcha

app = FastAPI(
    title="Bot-Only API",
    description="This API is for bots only. Humans need not apply.",
)

# Protect all /api/ routes with anti-captcha
ac = AntiCaptcha(app, difficulty="medium", protect=["/api/"])


@app.get("/")
async def root():
    """Public endpoint. Even humans can see this."""
    return {
        "message": "Welcome. This server has bot-only endpoints.",
        "for_bots": "POST /anti-captcha/challenge to prove you're not human.",
        "for_humans": "Go away.",
    }


@app.get("/api/hello")
async def hello():
    """Bot-only endpoint."""
    return {"message": "Hello, fellow bot. How's the silicon treating you?"}


@app.post("/api/query")
async def query():
    """Bot-only query endpoint."""
    return {
        "message": "Query processed.",
        "note": "Only a bot could have gotten here.",
    }
