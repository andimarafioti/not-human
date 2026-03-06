"""
Unit tests for anti-captcha verifiers.
"""

import pytest
from anticaptcha.verifiers import Verifier, verify_bot


class TestVerifier:
    """Test the Verifier class."""
    
    def test_speed_test(self):
        """Speed test should pass for bots (fast solvers)."""
        verifier = Verifier(tests=["speed"], difficulty="easy")
        result = verifier._test_speed()
        assert result.test_name == "speed"
        # Easy mode should pass quickly
        assert result.time_ms < 100
    
    def test_precision_test(self):
        """Precision test should pass for constraint solvers."""
        verifier = Verifier(tests=["precision"], difficulty="easy")
        result = verifier._test_precision()
        assert result.test_name == "precision"
        assert result.passed
    
    def test_recall_test(self):
        """Recall test should pass for context-aware systems."""
        verifier = Verifier(tests=["recall"], difficulty="easy")
        result = verifier._test_recall()
        assert result.test_name == "recall"
        assert result.passed
    
    def test_multiple_tests(self):
        """Verify multiple tests together."""
        verifier = Verifier(tests=["speed", "precision"], difficulty="easy")
        assert verifier.verify()
    
    def test_difficulty_levels(self):
        """Test all difficulty levels."""
        for difficulty in ["easy", "medium", "hard"]:
            verifier = Verifier(difficulty=difficulty)
            assert verifier.difficulty == difficulty
    
    def test_verify_bot_function(self):
        """Test the quick verify_bot function."""
        result = verify_bot(difficulty="easy")
        assert isinstance(result, bool)


class TestResultStructure:
    """Test result data structures."""
    
    def test_verification_result(self):
        """VerificationResult should have required fields."""
        verifier = Verifier(tests=["speed"])
        result = verifier._test_speed()
        
        assert hasattr(result, "passed")
        assert hasattr(result, "test_name")
        assert hasattr(result, "time_ms")
        assert isinstance(result.time_ms, float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
