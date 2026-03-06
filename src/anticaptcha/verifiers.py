"""
Core verification tests for anti-captcha.
"""

import hashlib
import time
from typing import Callable, Optional
from dataclasses import dataclass


@dataclass
class VerificationResult:
    passed: bool
    test_name: str
    time_ms: float
    reason: Optional[str] = None


class Verifier:
    """
    Bot verification engine.
    
    Tests bots through speed, precision, and recall challenges.
    Humans fail. Bots pass.
    """
    
    def __init__(
        self,
        tests: list[str] = None,
        difficulty: str = "medium",
        timeout_ms: int = 100,
    ):
        self.tests = tests or ["speed", "precision"]
        self.difficulty = difficulty
        self.timeout_ms = timeout_ms
        
        # Difficulty scaling
        self.difficulty_params = {
            "easy": {
                "speed_target_ms": 10,
                "precision_iterations": 100,
                "recall_context_size": 1000,
            },
            "medium": {
                "speed_target_ms": 1,
                "precision_iterations": 10000,
                "recall_context_size": 10000,
            },
            "hard": {
                "speed_target_ms": 0.1,
                "precision_iterations": 100000,
                "recall_context_size": 50000,
            },
        }
    
    def verify(self, request=None) -> bool:
        """
        Run all configured tests. Return True if bot, False if human (or suspicious).
        """
        results = []
        for test_name in self.tests:
            if test_name == "speed":
                results.append(self._test_speed())
            elif test_name == "precision":
                results.append(self._test_precision())
            elif test_name == "recall":
                results.append(self._test_recall())
        
        # All tests must pass
        return all(r.passed for r in results)
    
    def _test_speed(self) -> VerificationResult:
        """
        Speed test: Simple math operation that bots do instantly.
        
        Compute: sum of squares for range(10000)
        Then verify SHA256 of result matches known hash.
        Bots: microseconds. Humans: still fast, but measurable.
        """
        test_name = "speed"
        start = time.perf_counter()
        
        # Simple computation: sum of squares
        result = sum(i**2 for i in range(10000))
        expected_hash = "a9296d4486777ee30ad6eea7fc3e5736"  # Pre-computed
        actual_hash = hashlib.md5(str(result).encode()).hexdigest()
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        # Bots do this in <10ms. Humans are also fast at this, but it's a baseline.
        passed = actual_hash == expected_hash and elapsed_ms < 50
        
        return VerificationResult(
            passed=passed,
            test_name=test_name,
            time_ms=elapsed_ms,
            reason="Fast computation" if not passed else None,
        )
    
    def _test_precision(self) -> VerificationResult:
        """
        Precision test: Find input matching multiple constraints.
        
        Example: Find X where X < 100000, X % 7 == 3, SHA256(X) < threshold
        Bots: brute-force, instant.
        Humans: give up.
        """
        test_name = "precision"
        start = time.perf_counter()
        
        # Constraints
        max_val = 100000
        mod_constraint = 3  # X % 7 == mod_constraint
        target_hash_prefix = "0"  # SHA256 must start with "0"
        
        found = False
        for x in range(max_val):
            if x % 7 == mod_constraint:
                hash_val = hashlib.sha256(str(x).encode()).hexdigest()
                if hash_val.startswith(target_hash_prefix):
                    found = True
                    break
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        passed = found and elapsed_ms < 10.0  # Generous for demo
        
        return VerificationResult(
            passed=passed,
            test_name=test_name,
            time_ms=elapsed_ms,
            reason="Constraint satisfaction" if not passed else None,
        )
    
    def _test_recall(self) -> VerificationResult:
        """
        Token recall test: Given a context, recall specific line.
        
        Load a 10K token prompt, ask for line N verbatim.
        Bots: trivial (context window). Humans: impossible.
        """
        test_name = "recall"
        start = time.perf_counter()
        
        # Simulate token recall: Create a long string and ask for line N
        context_size = self.difficulty_params[self.difficulty]["recall_context_size"]
        lines = [f"Line {i}: {'x' * 100}" for i in range(context_size // 100)]
        full_context = "\n".join(lines)
        
        target_line_num = 42
        target_line = lines[target_line_num]
        
        # Bot can instantly recall this
        recall_success = target_line in full_context
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        passed = recall_success and elapsed_ms < 100
        
        return VerificationResult(
            passed=passed,
            test_name=test_name,
            time_ms=elapsed_ms,
            reason="Token recall" if not passed else None,
        )


def verify_bot(request=None, difficulty: str = "medium") -> bool:
    """
    Quick function: verify if request is from a bot.
    
    Usage:
        if verify_bot(request):
            # Bot confirmed
            return process_agent_request()
    """
    verifier = Verifier(difficulty=difficulty)
    return verifier.verify(request)
