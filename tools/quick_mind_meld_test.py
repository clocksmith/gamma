#!/usr/bin/env python3
"""
Quick Mind Meld Test Script
Tests mind_meld with available Ollama models
"""

import subprocess
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_test(name, models, strategy, steps=20, extra_args=None):
    """Run a single mind_meld test"""
    print(f"\n{'='*70}")
    print(f"Test: {name}")
    print(f"{'='*70}")

    cmd = [
        "python", "tools/run_mind_meld_cli.py",
        "--models"] + models + [
        "--strategy", strategy,
        "--steps", str(steps),
        "--temperature", "0.8",
        "--prompt", "In a world where two minds collaborate,"
    ]

    if extra_args:
        cmd.extend(extra_args)

    print(f"Command: {' '.join(cmd)}")
    print()

    try:
        subprocess.run(cmd, check=True)
        print(f"\n✓ {name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {name} failed: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n⚠ {name} interrupted by user")
        return False

def main():
    print("="*70)
    print("QUICK MIND MELD TEST SUITE")
    print("="*70)
    print("\nTesting with available Ollama models...")

    # Check if models are available
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if "gemma3:270m" not in result.stdout:
            print("⚠ Warning: gemma3:270m not found. You may need to adjust model names.")
    except FileNotFoundError:
        print("⚠ Warning: Ollama not found in PATH")

    tests_passed = 0
    tests_total = 0

    # Test 1: Small models with pattern-based swapping
    tests_total += 1
    if run_test(
        "Small Models - Pattern Based",
        ["ollama:gemma3:270m", "ollama:gemma3:1b-it-qat"],
        "pattern",
        steps=15
    ):
        tests_passed += 1

    # Test 2: Fixed interval swapping
    tests_total += 1
    if run_test(
        "Fixed Interval Swapping",
        ["ollama:gemma3:270m", "ollama:gemma3:1b-it-qat"],
        "fixed_interval",
        steps=20,
        extra_args=["--interval", "5"]
    ):
        tests_passed += 1

    # Test 3: Round robin with weighted averaging
    tests_total += 1
    if run_test(
        "Round Robin with Weighted Averaging",
        ["ollama:gemma3:270m", "ollama:gemma3:1b-it-qat"],
        "round_robin",
        steps=15,
        extra_args=["--use-weighted-average"]
    ):
        tests_passed += 1

    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Tests passed: {tests_passed}/{tests_total}")

    if tests_passed == tests_total:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"⚠ {tests_total - tests_passed} test(s) failed")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(130)
