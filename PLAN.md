# anti-captcha — Bot Verification Package

**Goal:** Small, viral Python/JS package that proves you're a bot (not a human). "Open the door for agents."

**Status:** Planning phase

---

## Phase 1: MVP (Weekend)

### Core Package Structure
```
anti-captcha/
├── pyproject.toml
├── README.md
├── src/anticaptcha/
│   ├── __init__.py
│   ├── verifiers.py          # speed, precision, patience, recall tests
│   ├── request_handler.py    # FastAPI/Flask middleware
│   └── cli.py               # Command-line demo
├── tests/
│   ├── test_speed.py
│   ├── test_precision.py
│   └── test_integration.py
└── examples/
    ├── flask_example.py
    └── fastapi_example.py
```

### Core Tests (Pick 3 for MVP)
1. **Speed Test** (`<1ms` solve)
   - Simple math: prime factorization, SHA256 collision detection
   - Humans can't solve in 1ms; bots destroy it
   
2. **Precision Test** (constraint satisfaction)
   - "Find X where SHA256(X) starts with '0xABC', X < 1000000, X % 7 == 3"
   - Bots: brute-force in microseconds
   - Humans: give up or think for hours

3. **Token Recall** (context extraction)
   - Load 10K token prompt, ask for line N verbatim
   - Bots: easy (context window); Humans: "what?"

### Deliverables
- [ ] `verify_bot(request)` function (returns True/False)
- [ ] 3 test implementations + difficulty scaling
- [ ] FastAPI/Flask middleware example
- [ ] CLI tool to test your own bot
- [ ] README with funny copy ("Sorry, you look too human")
- [ ] Publish to PyPI

### Success Metrics
- <100 lines of core logic
- Can paste into production in 5 minutes
- Works with any Python web framework

---

## Phase 2: Polish & Launch

### Messaging
- Twitter thread: "We're inverting CAPTCHA. Now your *bot* proves it's real."
- GitHub: Add Hacker News + Product Hunt tags
- Frame for agentic frameworks (Anthropic, LangChain, Pydantic AI)

### Optional Features
- Difficulty slider (easy for personal assistants, hard for big agents)
- Rate limiting per agent ID
- Logging/analytics ("what % of requests are bots?")
- JS version (for frontend APIs)

---

## Timeline
- **Today:** Plan + folder setup ✓
- **This weekend:** Core tests + packaging
- **Next week:** Polish + docs + launch

---

## Next Steps
1. Create `src/anticaptcha/__init__.py` with basic structure
2. Implement speed test (SHA256 brute-force with time constraint)
3. Implement precision test (math constraints)
4. Build FastAPI middleware example
5. Write README with killer copy

**Who runs it?** You say go → I build MVP this weekend.
