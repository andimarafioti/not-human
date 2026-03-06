"""
anti-captcha bot client.

Auto-solves challenges and manages tokens for API access.

Usage:
    from anticaptcha.client import BotClient

    client = BotClient("https://api.example.com")
    
    # Automatically solves the challenge and gets a token
    client.authenticate()
    
    # All subsequent requests include the bot token
    response = client.get("/api/agent/query")
    response = client.post("/api/agent/action", json={"task": "summarize"})
"""

import hashlib
import hmac
import time
from typing import Optional

try:
    import httpx
    _HTTP_LIB = "httpx"
except ImportError:
    try:
        import requests
        _HTTP_LIB = "requests"
    except ImportError:
        _HTTP_LIB = None


def _solve_instruction(instruction: str, previous_answers: list[str]) -> str:
    """Parse a challenge instruction and compute the answer."""
    
    # SHA256
    if "SHA256('" in instruction and "Return the hex digest" in instruction:
        value = instruction.split("SHA256('")[1].split("')")[0]
        return hashlib.sha256(value.encode()).hexdigest()
    
    # HMAC-SHA256
    if "HMAC-SHA256(" in instruction:
        key = instruction.split("key='")[1].split("'")[0]
        msg = instruction.split("msg='")[1].split("'")[0]
        return hmac.new(key.encode(), msg.encode(), hashlib.sha256).hexdigest()
    
    # Recall
    if "What was your answer to step" in instruction:
        step_num = int(instruction.split("step ")[1].split("?")[0])
        return previous_answers[step_num - 1] if step_num - 1 < len(previous_answers) else ""
    
    # Iterated hash
    if "repeated" in instruction and "times" in instruction:
        nonce = instruction.split("of '")[1].split("'")[0]
        count = int(instruction.split("repeated ")[1].split(" times")[0])
        result = nonce
        for _ in range(count):
            result = hashlib.sha256(result.encode()).hexdigest()
        return result
    
    # Final concatenation hash
    if "Concatenate ALL" in instruction:
        return hashlib.sha256("".join(previous_answers).encode()).hexdigest()
    
    raise ValueError(f"Unknown instruction: {instruction}")


class BotClient:
    """
    HTTP client with automatic anti-captcha solving.
    
    Handles challenge/response flow, caches tokens, and includes
    the X-Bot-Token header on all requests.
    """
    
    def __init__(self, base_url: str, auto_auth: bool = True):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None
        self.token_expires: Optional[float] = None
        
        if _HTTP_LIB == "httpx":
            self._session = httpx.Client(timeout=30)
        elif _HTTP_LIB == "requests":
            self._session = requests.Session()
        else:
            raise ImportError(
                "Install httpx or requests: pip install httpx\n"
                "Bots have dependencies too."
            )
        
        if auto_auth:
            self.authenticate()
    
    def authenticate(self) -> str:
        """
        Solve the anti-captcha challenge and obtain a bot token.
        Returns the token.
        """
        # Start challenge
        resp = self._raw_post("/anti-captcha/challenge")
        data = resp.json() if hasattr(resp, 'json') and callable(resp.json) else resp.json()
        
        if data.get("status") != "next_step":
            raise RuntimeError(f"Failed to start challenge: {data}")
        
        answers = []
        
        while data.get("status") == "next_step":
            answer = _solve_instruction(data["instruction"], answers)
            answers.append(answer)
            
            resp = self._raw_post("/anti-captcha/solve", json={
                "challenge_id": data["challenge_id"],
                "answer": answer,
            })
            data = resp.json() if hasattr(resp, 'json') and callable(resp.json) else resp.json()
        
        if data.get("status") == "passed":
            self.token = data["token"]
            self.token_expires = time.time() + data.get("expires_in", 3600)
            return self.token
        
        raise RuntimeError(f"Challenge failed: {data.get('message', 'unknown error')}")
    
    @property
    def headers(self) -> dict:
        """Headers with bot token."""
        h = {}
        if self.token:
            h["X-Bot-Token"] = self.token
        return h
    
    def get(self, path: str, **kwargs) -> object:
        """GET with bot token."""
        self._ensure_auth()
        url = self.base_url + path
        return self._session.get(url, headers=self.headers, **kwargs)
    
    def post(self, path: str, **kwargs) -> object:
        """POST with bot token."""
        self._ensure_auth()
        url = self.base_url + path
        return self._session.post(url, headers=self.headers, **kwargs)
    
    def _raw_post(self, path: str, **kwargs) -> object:
        """POST without bot token (for challenge endpoints)."""
        url = self.base_url + path
        return self._session.post(url, **kwargs)
    
    def _ensure_auth(self):
        """Re-authenticate if token is expired or missing."""
        if not self.token or (self.token_expires and time.time() > self.token_expires):
            self.authenticate()
