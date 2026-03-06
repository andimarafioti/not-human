"""
anti-captcha: The first CAPTCHA for bots.

Prove you're not human.
"""

from .challenge import ChallengeGenerator, Challenge
from .client import BotClient
from .server import AntiCaptcha
from .verifiers import Verifier, verify_bot

__version__ = "0.1.0"
__all__ = [
    "AntiCaptcha",
    "BotClient",
    "ChallengeGenerator",
    "Challenge",
    "Verifier",
    "verify_bot",
]
