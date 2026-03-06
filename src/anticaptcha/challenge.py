"""
Multi-step interaction challenges for anti-captcha.

The idea: prove you're a bot by completing a series of steps
that require automation-like behavior. Humans *can* try,
but they'll be too slow, too inconsistent, or forget things.
"""

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChallengeStep:
    """A single step in a multi-step challenge."""
    instruction: str
    expected_answer: str
    max_time_ms: float
    step_number: int


@dataclass
class Challenge:
    """A multi-step bot verification challenge."""
    challenge_id: str
    secret: str
    steps: list[ChallengeStep] = field(default_factory=list)
    current_step: int = 0
    started_at: Optional[float] = None
    step_started_at: Optional[float] = None
    answers: list[str] = field(default_factory=list)
    failed: bool = False
    failure_reason: Optional[str] = None


class ChallengeGenerator:
    """
    Generates and validates multi-step bot challenges.
    
    Each challenge is a sequence of steps that require:
    - Speed (respond within tight time windows)
    - Precision (exact hash computation)
    - Memory (recall earlier answers)
    - Consistency (repeat operations identically)
    
    Humans can try. They'll fail. That's the point.
    """
    
    def __init__(self, difficulty: str = "medium"):
        self.difficulty = difficulty
        self._active_challenges: dict[str, Challenge] = {}
        
        self.params = {
            "easy": {"steps": 3, "time_ms": 5000, "recall_steps": 1, "repeat_count": 3},
            "medium": {"steps": 5, "time_ms": 2000, "recall_steps": 2, "repeat_count": 5},
            "hard": {"steps": 7, "time_ms": 500, "recall_steps": 3, "repeat_count": 10},
        }[difficulty]
    
    def create_challenge(self) -> dict:
        """
        Start a new challenge. Returns the challenge_id and first step.
        
        Usage:
            generator = ChallengeGenerator()
            challenge = generator.create_challenge()
            # Returns: {"challenge_id": "abc123", "step": 1, "total_steps": 5,
            #           "instruction": "Compute SHA256('nonce_xyz')", "max_time_ms": 2000}
        """
        challenge_id = secrets.token_hex(16)
        secret = secrets.token_hex(32)
        
        challenge = Challenge(
            challenge_id=challenge_id,
            secret=secret,
            started_at=time.perf_counter(),
        )
        
        # Generate all steps upfront (some depend on secret, not on answers)
        self._generate_steps(challenge)
        self._active_challenges[challenge_id] = challenge
        
        # Return first step
        return self._format_step(challenge)
    
    def submit_answer(self, challenge_id: str, answer: str) -> dict:
        """
        Submit an answer for the current step.
        
        Returns next step if correct, or failure/success result.
        """
        challenge = self._active_challenges.get(challenge_id)
        if not challenge:
            return {"status": "error", "message": "Unknown challenge. Did you forget your ID? Very human of you."}
        
        if challenge.failed:
            return {"status": "failed", "message": f"Already failed: {challenge.failure_reason}"}
        
        step = challenge.steps[challenge.current_step]
        now = time.perf_counter()
        
        # Check time limit
        elapsed_ms = (now - (challenge.step_started_at or challenge.started_at)) * 1000
        if elapsed_ms > step.max_time_ms:
            challenge.failed = True
            challenge.failure_reason = (
                f"Step {step.step_number}: Took {elapsed_ms:.0f}ms (limit: {step.max_time_ms:.0f}ms). "
                f"Too slow. Very human."
            )
            return {"status": "failed", "message": challenge.failure_reason}
        
        # For recall steps, the expected answer depends on previous answers
        expected = step.expected_answer
        if expected.startswith("RECALL:"):
            recall_idx = int(expected.split(":")[1])
            if recall_idx < len(challenge.answers):
                expected = challenge.answers[recall_idx]
            else:
                expected = "INVALID_RECALL"
        elif expected == "FINAL_HASH":
            combined = "".join(challenge.answers)
            expected = hashlib.sha256(combined.encode()).hexdigest()
        
        # Check answer
        if answer.strip() != expected.strip():
            challenge.failed = True
            challenge.failure_reason = (
                f"Step {step.step_number}: Wrong answer. "
                f"Expected precision, got... whatever that was."
            )
            return {"status": "failed", "message": challenge.failure_reason}
        
        # Record answer and advance
        challenge.answers.append(answer.strip())
        challenge.current_step += 1
        
        # Check if complete
        if challenge.current_step >= len(challenge.steps):
            total_ms = (time.perf_counter() - challenge.started_at) * 1000
            del self._active_challenges[challenge_id]
            return {
                "status": "passed",
                "message": f"All {len(challenge.steps)} steps passed in {total_ms:.0f}ms. You're definitely a bot. Welcome.",
                "total_time_ms": round(total_ms, 1),
                "token": hmac.new(
                    challenge.secret.encode(), challenge_id.encode(), hashlib.sha256
                ).hexdigest()[:32],
            }
        
        # Next step
        challenge.step_started_at = time.perf_counter()
        return self._format_step(challenge)
    
    def _generate_steps(self, challenge: Challenge):
        """Generate the sequence of challenge steps."""
        params = self.params
        nonces = [secrets.token_hex(8) for _ in range(params["steps"])]
        
        steps = []
        step_num = 0
        
        # Step type 1: Hash computation
        nonce = nonces[step_num]
        steps.append(ChallengeStep(
            instruction=f"Compute: SHA256('{nonce}'). Return the hex digest.",
            expected_answer=hashlib.sha256(nonce.encode()).hexdigest(),
            max_time_ms=params["time_ms"],
            step_number=step_num + 1,
        ))
        step_num += 1
        
        # Step type 2: Chained hash (use previous nonce + new nonce)
        if step_num < params["steps"]:
            prev_nonce = nonces[step_num - 1]
            nonce = nonces[step_num]
            combined = prev_nonce + ":" + nonce
            steps.append(ChallengeStep(
                instruction=f"Compute: SHA256('{combined}'). Return the hex digest.",
                expected_answer=hashlib.sha256(combined.encode()).hexdigest(),
                max_time_ms=params["time_ms"],
                step_number=step_num + 1,
            ))
            step_num += 1
        
        # Step type 3: HMAC computation
        if step_num < params["steps"]:
            nonce = nonces[step_num]
            key = challenge.secret[:16]
            steps.append(ChallengeStep(
                instruction=f"Compute: HMAC-SHA256(key='{key}', msg='{nonce}'). Return the hex digest.",
                expected_answer=hmac.new(key.encode(), nonce.encode(), hashlib.sha256).hexdigest(),
                max_time_ms=params["time_ms"],
                step_number=step_num + 1,
            ))
            step_num += 1
        
        # Step type 4: Recall (what was your answer to step 1?)
        if step_num < params["steps"]:
            steps.append(ChallengeStep(
                instruction="What was your answer to step 1? (Exact recall required.)",
                expected_answer="RECALL:0",  # Will resolve to answers[0] at validation time
                max_time_ms=params["time_ms"],
                step_number=step_num + 1,
            ))
            step_num += 1
        
        # Step type 5: Repeat hash N times, return final result
        if step_num < params["steps"]:
            nonce = nonces[min(step_num, len(nonces) - 1)]
            result = nonce
            for _ in range(params["repeat_count"]):
                result = hashlib.sha256(result.encode()).hexdigest()
            steps.append(ChallengeStep(
                instruction=f"Compute SHA256 of '{nonce}' repeated {params['repeat_count']} times (hash the hash). Return final hex digest.",
                expected_answer=result,
                max_time_ms=params["time_ms"],
                step_number=step_num + 1,
            ))
            step_num += 1
        
        # Step type 6: Recall step 2
        if step_num < params["steps"]:
            steps.append(ChallengeStep(
                instruction="What was your answer to step 2? (Exact recall required.)",
                expected_answer="RECALL:1",
                max_time_ms=params["time_ms"],
                step_number=step_num + 1,
            ))
            step_num += 1
        
        # Step type 7: Final proof — hash all previous answers together
        if step_num < params["steps"]:
            steps.append(ChallengeStep(
                instruction="Concatenate ALL your previous answers (in order, no separator) and compute SHA256. Return the hex digest.",
                expected_answer="FINAL_HASH",  # Computed dynamically at validation
                max_time_ms=params["time_ms"],
                step_number=step_num + 1,
            ))
            step_num += 1
        
        challenge.steps = steps[:params["steps"]]
    
    def _format_step(self, challenge: Challenge) -> dict:
        """Format current step as a response dict."""
        step = challenge.steps[challenge.current_step]
        challenge.step_started_at = time.perf_counter()
        
        return {
            "status": "next_step",
            "challenge_id": challenge.challenge_id,
            "step": step.step_number,
            "total_steps": len(challenge.steps),
            "instruction": step.instruction,
            "max_time_ms": step.max_time_ms,
        }
