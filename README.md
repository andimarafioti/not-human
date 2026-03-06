# not-human

The first CAPTCHA for bots. Prove you're not human.

```python
from anticaptcha.server import AntiCaptcha
from fastapi import FastAPI

app = FastAPI()
AntiCaptcha(app, difficulty="medium", protect=["/api/"])

# Humans get: 403 "Complete the challenge first."
# Bots get: instant access after solving a multi-step crypto challenge.
```

### Get it

```bash
pip install not-human
```

---

## The Problem

You built an agentic API. You *want* bots to access it. But you need to verify that incoming requests are actually from autonomous systems, not humans pretending to be bots.

Existing CAPTCHAs block bots and invite humans.

**not-human inverts that.**

---

## How It Works

A multi-step cryptographic challenge that bots solve instantly and humans can't.

1. **`POST /anti-captcha/challenge`** — Get a challenge (5-7 steps)
2. **Each step:** SHA256, HMAC, chained hashes, recall previous answers
3. **Time limit per step:** 500ms (hard), 2s (medium), 5s (easy)
4. **Pass all steps** → get an `X-Bot-Token` (valid 1 hour)
5. **Include token** in all subsequent requests

### Why humans fail

- Step 1: "Compute SHA256('a9f3e2b1c8d74560')" — you have 2 seconds
- Step 4: "What was your answer to step 1?" — exact recall required
- Step 7: "Concatenate ALL previous answers and hash them" — good luck

Bots: 0.02ms per step. Humans: keyboard not fast enough.

---

## Server (3 lines)

```python
from fastapi import FastAPI
from anticaptcha.server import AntiCaptcha

app = FastAPI()
AntiCaptcha(app, difficulty="medium", protect=["/api/"])

@app.get("/api/hello")
async def hello():
    return {"message": "Hello, fellow bot."}
```

Unprotected request:
```bash
curl http://localhost:8000/api/hello
# 403: "No X-Bot-Token header. Complete the challenge first."
```

---

## Bot Client (2 lines)

```python
from anticaptcha.client import BotClient

client = BotClient("http://localhost:8000")  # auto-solves challenge
resp = client.get("/api/hello")              # 200: "Hello, fellow bot."
```

The client automatically:
1. Requests a challenge
2. Solves all steps (SHA256, HMAC, recall, chained hashes)
3. Caches the token
4. Re-authenticates when token expires

---

## CLI

Watch a bot solve it:
```bash
anticaptcha solve --difficulty hard

🤖 anti-captcha bot solver (hard)
--- Step 1/7 (max 500ms) ---
  📋 Compute: SHA256('ec77e667aeac6a69'). Return the hex digest.
  🤖 92f1f0f98dc580f1f5650d33f5b57e9e...
  ⚡ 0.01ms

[...5 more steps...]

✓ All 7 steps passed in 0ms. You're definitely a bot. Welcome.
```

Try it yourself (you'll fail):
```bash
anticaptcha challenge --difficulty easy

🤖 anti-captcha challenge (easy)
Prove you're a bot. Complete each step within the time limit.

--- Step 1/3 (max 5000ms) ---
  Compute: SHA256('929cee29da39b727'). Return the hex digest.

  Your answer: uhhhh
✗ Wrong answer. Expected precision, got... whatever that was.
```

---

## Configuration

```python
AntiCaptcha(
    app,
    difficulty="medium",       # easy (3 steps, 5s), medium (5 steps, 2s), hard (7 steps, 500ms)
    protect=["/api/"],         # URL prefixes to gate
    token_ttl_seconds=3600,    # Token validity (default: 1 hour)
)
```

---

## Who Should Use This?

- **Agentic APIs** — Gate endpoints behind bot verification
- **Agent frameworks** — Anthropic, LangChain, Pydantic AI, CrewAI
- **Internal tools** — Verify requests are from automation, not manual curls
- **Fun** — Flip the script on the internet's most annoying interaction pattern

---

## License

MIT. Use it, fork it, make it funnier.
