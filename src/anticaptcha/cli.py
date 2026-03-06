"""
CLI for anti-captcha.

Two modes:
  anticaptcha challenge  — Interactive: try to prove you're a bot (you'll fail)
  anticaptcha solve      — Automated: let the bot client solve it for you
"""

import hashlib
import hmac
import sys
import time

from .challenge import ChallengeGenerator


def solve_step(instruction: str, previous_answers: list[str]) -> str:
    """
    Bot solver: parses the instruction and computes the answer.
    This is what an agent would do. Humans... good luck.
    """
    instruction = instruction.strip()
    
    # SHA256 computation
    if instruction.startswith("Compute: SHA256('") and instruction.endswith("'). Return the hex digest."):
        value = instruction.split("SHA256('")[1].split("')")[0]
        return hashlib.sha256(value.encode()).hexdigest()
    
    # HMAC computation
    if instruction.startswith("Compute: HMAC-SHA256("):
        # Parse key and msg from: HMAC-SHA256(key='xxx', msg='yyy')
        key = instruction.split("key='")[1].split("'")[0]
        msg = instruction.split("msg='")[1].split("'")[0]
        return hmac.new(key.encode(), msg.encode(), hashlib.sha256).hexdigest()
    
    # Recall
    if "What was your answer to step" in instruction:
        step_num = int(instruction.split("step ")[1].split("?")[0])
        idx = step_num - 1
        if idx < len(previous_answers):
            return previous_answers[idx]
        return "UNKNOWN"
    
    # Repeated hash
    if "repeated" in instruction and "times" in instruction:
        nonce = instruction.split("of '")[1].split("'")[0]
        count = int(instruction.split("repeated ")[1].split(" times")[0])
        result = nonce
        for _ in range(count):
            result = hashlib.sha256(result.encode()).hexdigest()
        return result
    
    # Final hash of all answers
    if "Concatenate ALL" in instruction:
        combined = "".join(previous_answers)
        return hashlib.sha256(combined.encode()).hexdigest()
    
    return "UNKNOWN"


def cmd_challenge(difficulty: str):
    """Interactive mode: YOU try to solve it. Good luck, human."""
    
    print(f"\n🤖 anti-captcha challenge ({difficulty})")
    print("=" * 50)
    print("Prove you're a bot. Complete each step within the time limit.")
    print("Copy-paste is allowed. Being slow is not.\n")
    
    gen = ChallengeGenerator(difficulty=difficulty)
    result = gen.create_challenge()
    
    while result["status"] == "next_step":
        print(f"--- Step {result['step']}/{result['total_steps']} (max {result['max_time_ms']:.0f}ms) ---")
        print(f"  {result['instruction']}")
        print()
        
        try:
            answer = input("  Your answer: ")
        except (EOFError, KeyboardInterrupt):
            print("\n\nGave up? Very human of you.")
            return 1
        
        result = gen.submit_answer(result["challenge_id"], answer)
    
    print()
    if result["status"] == "passed":
        print(f"✓ {result['message']}")
        print(f"  Token: {result['token']}")
        return 0
    else:
        print(f"✗ {result['message']}")
        return 1


def cmd_solve(difficulty: str):
    """Automated mode: let the bot client solve it."""
    
    print(f"\n🤖 anti-captcha bot solver ({difficulty})")
    print("=" * 50)
    print("Watch the bot breeze through it.\n")
    
    gen = ChallengeGenerator(difficulty=difficulty)
    result = gen.create_challenge()
    
    answers = []
    
    while result["status"] == "next_step":
        print(f"--- Step {result['step']}/{result['total_steps']} (max {result['max_time_ms']:.0f}ms) ---")
        print(f"  📋 {result['instruction']}")
        
        start = time.perf_counter()
        answer = solve_step(result["instruction"], answers)
        elapsed = (time.perf_counter() - start) * 1000
        
        print(f"  🤖 {answer[:32]}{'...' if len(answer) > 32 else ''}")
        print(f"  ⚡ {elapsed:.2f}ms")
        print()
        
        answers.append(answer)
        result = gen.submit_answer(result["challenge_id"], answer)
    
    if result["status"] == "passed":
        print(f"✓ {result['message']}")
        print(f"  Token: {result['token']}")
        return 0
    else:
        print(f"✗ {result['message']}")
        return 1


def main():
    difficulty = "medium"
    mode = "solve"  # Default: show the bot solving it
    
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        print("Usage: anticaptcha [challenge|solve] [--difficulty easy|medium|hard]")
        print()
        print("  challenge  — YOU try to solve it (interactive, good luck)")
        print("  solve      — Watch the bot solve it (automated, effortless)")
        print()
        print("Options:")
        print("  --difficulty  easy, medium, or hard (default: medium)")
        return 0
    
    if "challenge" in args:
        mode = "challenge"
    elif "solve" in args:
        mode = "solve"
    
    if "--difficulty" in args:
        idx = args.index("--difficulty")
        if idx + 1 < len(args):
            difficulty = args[idx + 1]
    
    if mode == "challenge":
        return cmd_challenge(difficulty)
    else:
        return cmd_solve(difficulty)


if __name__ == "__main__":
    sys.exit(main())
