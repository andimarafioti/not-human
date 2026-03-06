"""
Demo: bot client auto-solving anti-captcha and accessing protected API.

Run the server first:
    uvicorn demo_server:app --port 8000

Then:
    python demo_client.py
"""

from anticaptcha.client import BotClient


def main():
    print("🤖 Connecting to bot-only API...\n")
    
    # Auto-authenticates on creation (solves challenge)
    client = BotClient("http://localhost:8000")
    
    print(f"✓ Authenticated! Token: {client.token[:16]}...")
    print(f"  Expires in: {client.token_expires - __import__('time').time():.0f}s\n")
    
    # Access protected endpoints
    print("--- Accessing /api/hello ---")
    resp = client.get("/api/hello")
    print(f"  {resp.status_code}: {resp.json()}\n")
    
    print("--- Accessing /api/query ---")
    resp = client.post("/api/query")
    print(f"  {resp.status_code}: {resp.json()}\n")
    
    print("✓ All requests succeeded. Humans could never.")


if __name__ == "__main__":
    main()
