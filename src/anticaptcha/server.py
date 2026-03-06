"""
anti-captcha server endpoints.

Drop these into any FastAPI/Flask app to gate endpoints behind bot verification.

Usage:
    from anticaptcha.server import AntiCaptcha

    app = FastAPI()
    ac = AntiCaptcha(app, difficulty="medium", protect=["/api/"])
    
    @app.post("/api/agent/query")
    async def query():
        return {"status": "bot verified, processing"}
"""

import hashlib
import hmac
import time
from typing import Optional

from .challenge import ChallengeGenerator


class AntiCaptcha:
    """
    Drop-in bot verification for FastAPI apps.
    
    Adds:
      POST /anti-captcha/challenge     — Start a challenge
      POST /anti-captcha/solve         — Submit answer for current step
      GET  /anti-captcha/verify/{token} — Check if a token is valid
    
    Protected routes require `X-Bot-Token` header with a valid token.
    """
    
    def __init__(
        self,
        app=None,
        difficulty: str = "medium",
        protect: list[str] = None,
        token_ttl_seconds: int = 3600,
        secret_key: str = "anti-captcha-default-secret",
    ):
        self.difficulty = difficulty
        self.protect = protect or ["/api/"]
        self.token_ttl = token_ttl_seconds
        self.secret_key = secret_key
        self._generator = ChallengeGenerator(difficulty=difficulty)
        self._valid_tokens: dict[str, float] = {}  # token → expiry timestamp
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Attach anti-captcha routes and middleware to a FastAPI app."""
        from fastapi import Request
        from fastapi.responses import JSONResponse
        
        @app.post("/anti-captcha/challenge")
        async def start_challenge():
            """Start a new bot verification challenge."""
            result = self._generator.create_challenge()
            return result
        
        @app.post("/anti-captcha/solve")
        async def solve_step(request: Request):
            """Submit an answer for the current challenge step."""
            body = await request.json()
            challenge_id = body.get("challenge_id")
            answer = body.get("answer")
            
            if not challenge_id or not answer:
                return JSONResponse(
                    {"error": "Missing challenge_id or answer. Humans forget things. Bots don't."},
                    status_code=400,
                )
            
            result = self._generator.submit_answer(challenge_id, answer)
            
            # If passed, register the token
            if result.get("status") == "passed":
                token = result["token"]
                self._valid_tokens[token] = time.time() + self.token_ttl
                result["expires_in"] = self.token_ttl
                result["header"] = "X-Bot-Token"
                result["usage"] = f"Include header 'X-Bot-Token: {token}' in subsequent requests."
            
            return result
        
        @app.get("/anti-captcha/verify/{token}")
        async def verify_token(token: str):
            """Check if a token is valid (for debugging)."""
            if self._is_valid_token(token):
                return {"valid": True, "message": "Token verified. You're a bot."}
            return JSONResponse(
                {"valid": False, "message": "Invalid or expired token. Try the challenge again."},
                status_code=401,
            )
        
        @app.middleware("http")
        async def check_bot_token(request: Request, call_next):
            """Gate protected routes behind bot verification."""
            path = request.url.path
            
            # Skip anti-captcha endpoints themselves
            if path.startswith("/anti-captcha/"):
                return await call_next(request)
            
            # Skip unprotected paths
            if not any(path.startswith(p) for p in self.protect):
                return await call_next(request)
            
            # Check token
            token = request.headers.get("X-Bot-Token")
            if not token:
                return JSONResponse(
                    {
                        "error": "No X-Bot-Token header. Complete the challenge first.",
                        "challenge_url": "/anti-captcha/challenge",
                        "hint": "POST /anti-captcha/challenge to start. Humans need not apply.",
                    },
                    status_code=403,
                )
            
            if not self._is_valid_token(token):
                return JSONResponse(
                    {
                        "error": "Invalid or expired token.",
                        "challenge_url": "/anti-captcha/challenge",
                        "hint": "Your token expired or was never valid. Try the challenge again.",
                    },
                    status_code=401,
                )
            
            return await call_next(request)
    
    def _is_valid_token(self, token: str) -> bool:
        """Check if a token exists and hasn't expired."""
        expiry = self._valid_tokens.get(token)
        if expiry is None:
            return False
        if time.time() > expiry:
            del self._valid_tokens[token]
            return False
        return True
    
    def _cleanup_expired(self):
        """Remove expired tokens."""
        now = time.time()
        expired = [t for t, exp in self._valid_tokens.items() if now > exp]
        for t in expired:
            del self._valid_tokens[t]
