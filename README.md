# anti-captcha

The first CAPTCHA for bots. Prove you're not human.

```python
from anticaptcha import verify_bot

if verify_bot(request):
    # Agent access granted. Humans need not apply.
    return process_request()
else:
    return "Sorry, you look too human. Try upgrading to an LLM."
```

---

## The Problem

You built an agentic API. You *want* bots to access it. But you need to filter out humans pretending to be bots, or verify that incoming requests are actually from autonomous systems.

Existing CAPTCHAs do the opposite: they block bots, invite humans.

**anti-captcha inverts that.**

---

## How It Works

Three configurable tests. Bots pass them instantly. Humans... don't.

### Speed Test
Solve a cryptographic puzzle in <1ms.
- Bots: ✓ (microseconds)
- Humans: ✗ (try 30 seconds)

### Precision Test
Find an input matching N constraints simultaneously.
- Bots: ✓ (brute force, instant)
- Humans: ✗ (give up)

### Token Recall
Given a 10K token context, cite line 7342 verbatim.
- Bots: ✓ (context window, trivial)
- Humans: ✗ (you're not a calculator)

---

## Install

```bash
pip install anticaptcha
```

---

## Quick Start

### FastAPI
```python
from fastapi import FastAPI, HTTPException
from anticaptcha import verify_bot_middleware

app = FastAPI()
app.add_middleware(verify_bot_middleware)

@app.post("/api/agent")
async def agent_endpoint():
    return {"status": "human filter bypassed"}
```

### Flask
```python
from flask import Flask, request
from anticaptcha import verify_bot

app = Flask(__name__)

@app.before_request
def check_bot():
    if not verify_bot(request):
        return "Humans not allowed here", 403
```

### CLI
```bash
anticaptcha test --difficulty hard
# Running speed test...
# Running precision test...
# Running token recall test...
# ✓ All tests passed. You're definitely a bot.
```

---

## Customization

```python
from anticaptcha import Verifier

verifier = Verifier(
    tests=['speed', 'precision', 'recall'],
    difficulty='medium',  # easy, medium, hard
    timeout_ms=100,
)

is_bot = verifier.verify(request)
```

---

## Who Should Use This?

- **Agentic APIs** — Filter out human traffic, prioritize agents
- **Agent Frameworks** — Anthropic Claude Computer Use, Pydantic AI, LangChain
- **Internal Tools** — Verify that scripts calling your endpoints are actually automation, not manual curls
- **Fun** — Flip the script on the internet's most annoying interaction pattern

---

## License

MIT. Use it, fork it, make it funnier.

---

## Status

🚀 MVP coming this weekend.
