"""
Request handlers and middleware for anti-captcha integration.
"""

from .verifiers import Verifier


def verify_bot_middleware(app, difficulty: str = "medium"):
    """
    FastAPI/Starlette middleware factory.
    
    Usage:
        from fastapi import FastAPI
        from anticaptcha import verify_bot_middleware
        
        app = FastAPI()
        app.add_middleware(verify_bot_middleware, difficulty="medium")
    """
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse
    
    class BotVerificationMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            verifier = Verifier(difficulty=difficulty)
            
            # Skip verification for non-API endpoints
            if not request.url.path.startswith("/api/"):
                return await call_next(request)
            
            # Verify bot
            if not verifier.verify(request):
                return JSONResponse(
                    {"error": "Sorry, you look too human. Try upgrading to an LLM."},
                    status_code=403,
                )
            
            return await call_next(request)
    
    return BotVerificationMiddleware(app)


def verify_bot_flask(app, difficulty: str = "medium"):
    """
    Flask middleware.
    
    Usage:
        from flask import Flask
        from anticaptcha import verify_bot_flask
        
        app = Flask(__name__)
        verify_bot_flask(app, difficulty="medium")
        
        @app.route("/api/agent", methods=["POST"])
        def agent():
            return {"status": "ok"}
    """
    from flask import request, jsonify
    
    @app.before_request
    def check_bot():
        if not request.path.startswith("/api/"):
            return
        
        verifier = Verifier(difficulty=difficulty)
        if not verifier.verify(request):
            return jsonify(
                {"error": "Sorry, you look too human. Try upgrading to an LLM."}
            ), 403
    
    return app
