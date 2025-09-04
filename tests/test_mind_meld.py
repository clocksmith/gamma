#!/usr/bin/env python3
"""Quick test script for Mind Meld fixed interval swapping"""

import subprocess
import sys

# Test command for fixed interval swapping every token
cmd = [
    "python3", "mind_meld_cli.py",
    "--models", "google/gemma-3-1b-it", "google/gemma-2-2b-it",
    "--strategy", "fixed",
    "--interval", "1",
    "--steps", "10",
    "--prompt", "Hello world",
    "--verbose"
]

print("Testing Mind Meld with fixed interval (swap every token)...")
print("Command:", " ".join(cmd))
print("=" * 70)

try:
    result = subprocess.run(cmd, capture_output=False, text=True)
    sys.exit(result.returncode)
except KeyboardInterrupt:
    print("\n\nTest interrupted by user")
    sys.exit(1)
except Exception as e:
    print(f"Error running test: {e}")
    sys.exit(1)