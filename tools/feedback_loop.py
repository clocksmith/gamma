#!/usr/bin/env python3
"""
GAMMA Feedback Loop - Automated Testing and Fixing
Runs tests, analyzes failures, attempts fixes, and iterates.

Usage:
    python tools/feedback_loop.py [options]

Options:
    --max-iterations N    Maximum number of fix iterations (default: 5)
    --test-command CMD    Custom test command (default: ./run_tests.sh)
    --auto-fix            Automatically apply suggested fixes (default: prompt)
    --verbose             Show detailed output
    --log-file FILE       Save detailed logs to file
    --test-filter PATTERN Only run tests matching pattern
"""

import argparse
import subprocess
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add src to path
ROOT_DIR = Path(__file__).parent.parent
SRC_DIR = ROOT_DIR / 'src'
sys.path.insert(0, str(SRC_DIR))

from log_analyzer import LogAnalyzer, TestFailure
from auto_fixer import AutoFixer


class FeedbackLoop:
    """Main feedback loop for testing and fixing GAMMA."""

    def __init__(self,
                 max_iterations: int = 5,
                 test_command: str = "./run_tests.sh",
                 auto_fix: bool = False,
                 verbose: bool = False,
                 log_file: Optional[str] = None,
                 test_filter: Optional[str] = None,
                 run_live: bool = False,
                 live_modes: Optional[List[str]] = None,
                 live_timeout: int = 30):
        self.max_iterations = max_iterations
        self.test_command = test_command
        self.auto_fix = auto_fix
        self.verbose = verbose
        self.test_filter = test_filter
        self.run_live = run_live
        self.live_modes = live_modes or ['game --help', 'comparison --help', 'mind-meld --help']
        self.live_timeout = live_timeout

        # Initialize logging
        self.log_file = log_file
        if self.log_file:
            self.log_handle = open(self.log_file, 'w')
        else:
            self.log_handle = None

        # Initialize components
        self.analyzer = LogAnalyzer()
        self.fixer = AutoFixer(auto_apply=auto_fix)

        # Track history
        self.iteration_history = []
        self.all_failures = set()

    def log(self, message: str, level: str = "INFO"):
        """Log a message to console and/or file."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {level}: {message}"

        if self.verbose or level in ["ERROR", "SUCCESS", "ITERATION"]:
            print(formatted)

        if self.log_handle:
            self.log_handle.write(formatted + "\n")
            self.log_handle.flush()

    def run_tests(self) -> tuple[bool, str, str]:
        """Run tests and capture output."""
        self.log("Running tests...", "INFO")

        # Build command
        cmd = self.test_command
        if self.test_filter:
            cmd = f"pytest -v -k '{self.test_filter}' tests/"

        # Run tests
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(ROOT_DIR),
                timeout=300  # 5 minute timeout
            )

            success = result.returncode == 0
            stdout = result.stdout
            stderr = result.stderr

            if success:
                self.log("Tests passed!", "SUCCESS")
            else:
                self.log(f"Tests failed with exit code {result.returncode}", "ERROR")

            return success, stdout, stderr

        except subprocess.TimeoutExpired:
            self.log("Test execution timed out!", "ERROR")
            return False, "", "TIMEOUT: Test execution exceeded 5 minutes"
        except Exception as e:
            self.log(f"Error running tests: {e}", "ERROR")
            return False, "", str(e)

    def analyze_failures(self, stdout: str, stderr: str) -> List[TestFailure]:
        """Analyze test output to identify failures."""
        self.log("Analyzing failures...", "INFO")

        combined_output = stdout + "\n" + stderr
        failures = self.analyzer.parse_test_output(combined_output)

        if failures:
            self.log(f"Found {len(failures)} failure(s):", "ERROR")
            for i, failure in enumerate(failures, 1):
                self.log(f"  {i}. {failure.test_name}: {failure.error_type}", "ERROR")
                if self.verbose:
                    self.log(f"     File: {failure.file_path}:{failure.line_number}", "INFO")
                    self.log(f"     Message: {failure.error_message[:100]}...", "INFO")
        else:
            self.log("No specific failures identified in output", "INFO")

        return failures

    def attempt_fixes(self, failures: List[TestFailure]) -> Dict[str, Any]:
        """Attempt to fix identified failures."""
        self.log(f"Attempting to fix {len(failures)} failure(s)...", "INFO")

        fix_results = {
            'applied': [],
            'skipped': [],
            'failed': []
        }

        for failure in failures:
            try:
                # Generate fix suggestions
                suggestions = self.fixer.suggest_fixes(failure)

                if not suggestions:
                    self.log(f"  No fixes available for: {failure.test_name}", "INFO")
                    fix_results['skipped'].append({
                        'test': failure.test_name,
                        'reason': 'No suggestions generated'
                    })
                    continue

                # Apply or prompt for fixes
                for suggestion in suggestions:
                    if self.auto_fix:
                        # Auto-apply
                        success = self.fixer.apply_fix(suggestion)
                        if success:
                            self.log(f"  ✓ Applied fix: {suggestion['description']}", "SUCCESS")
                            fix_results['applied'].append(suggestion)
                        else:
                            self.log(f"  ✗ Failed to apply: {suggestion['description']}", "ERROR")
                            fix_results['failed'].append(suggestion)
                    else:
                        # Prompt user
                        self.log(f"  Suggested fix: {suggestion['description']}", "INFO")
                        self.log(f"    File: {suggestion['file_path']}", "INFO")

                        response = input("    Apply this fix? [y/N]: ").strip().lower()
                        if response == 'y':
                            success = self.fixer.apply_fix(suggestion)
                            if success:
                                self.log(f"  ✓ Applied", "SUCCESS")
                                fix_results['applied'].append(suggestion)
                            else:
                                self.log(f"  ✗ Failed to apply", "ERROR")
                                fix_results['failed'].append(suggestion)
                        else:
                            fix_results['skipped'].append(suggestion)

            except Exception as e:
                self.log(f"  Error fixing {failure.test_name}: {e}", "ERROR")
                fix_results['failed'].append({
                    'test': failure.test_name,
                    'error': str(e)
                })

        return fix_results

    def run_live_execution(self, mode: str) -> tuple[bool, str, str]:
        """Run gamma.py in a specific mode end-to-end."""
        self.log(f"Running live execution: gamma.py {mode}", "INFO")

        # Build command
        cmd = f"python gamma.py {mode}"

        # For non-help modes, add timeout and provide stdin
        stdin_input = None
        if '--help' not in mode and '--version' not in mode:
            # For interactive modes, provide automatic inputs to exit gracefully
            stdin_input = "\n/quit\nexit\nq\n"

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(ROOT_DIR),
                timeout=self.live_timeout,
                input=stdin_input
            )

            success = result.returncode == 0
            stdout = result.stdout
            stderr = result.stderr

            if success:
                self.log(f"  ✓ Live execution succeeded: {mode}", "SUCCESS")
            else:
                self.log(f"  ✗ Live execution failed: {mode} (exit code: {result.returncode})", "ERROR")

            return success, stdout, stderr

        except subprocess.TimeoutExpired:
            self.log(f"  ⚠ Live execution timed out: {mode}", "ERROR")
            return False, "", f"TIMEOUT: Execution exceeded {self.live_timeout} seconds"
        except Exception as e:
            self.log(f"  ✗ Error in live execution: {e}", "ERROR")
            return False, "", str(e)

    def run_all_live_modes(self) -> tuple[bool, List[str], List[str]]:
        """Run all configured live modes."""
        self.log("Running live end-to-end executions...", "INFO")

        all_success = True
        all_stdout = []
        all_stderr = []

        for mode in self.live_modes:
            success, stdout, stderr = self.run_live_execution(mode)
            all_stdout.append(f"=== MODE: {mode} ===\n{stdout}")
            all_stderr.append(f"=== MODE: {mode} ===\n{stderr}")

            if not success:
                all_success = False

        return all_success, all_stdout, all_stderr

    def run_iteration(self, iteration: int) -> bool:
        """Run one iteration of the feedback loop."""
        self.log("=" * 80, "ITERATION")
        self.log(f"ITERATION {iteration}/{self.max_iterations}", "ITERATION")
        self.log("=" * 80, "ITERATION")

        iteration_data = {
            'iteration': iteration,
            'timestamp': datetime.now().isoformat(),
            'test_passed': False,
            'live_passed': False,
            'failures': [],
            'fixes_applied': []
        }

        all_passed = True

        # Run live execution if enabled
        if self.run_live:
            live_success, live_stdout, live_stderr = self.run_all_live_modes()
            iteration_data['live_passed'] = live_success

            if not live_success:
                all_passed = False
                # Analyze live execution failures
                combined_live = '\n'.join(live_stdout) + '\n' + '\n'.join(live_stderr)
                live_failures = self.analyze_failures(combined_live, '')
                iteration_data['failures'].extend([f.to_dict() for f in live_failures])

                # Track unique failures
                for failure in live_failures:
                    failure_key = f"{failure.test_name}:{failure.error_type}"
                    self.all_failures.add(failure_key)

        # Run tests
        test_success, stdout, stderr = self.run_tests()
        iteration_data['test_passed'] = test_success

        if not test_success:
            all_passed = False
            # Analyze test failures
            test_failures = self.analyze_failures(stdout, stderr)
            iteration_data['failures'].extend([f.to_dict() for f in test_failures])

            # Track unique failures
            for failure in test_failures:
                failure_key = f"{failure.test_name}:{failure.error_type}"
                self.all_failures.add(failure_key)

        # If everything passed, we're done
        if all_passed:
            self.iteration_history.append(iteration_data)
            return True

        # Get all failures (deduplicated)
        all_failure_dicts = iteration_data['failures']
        unique_failures = {}
        for f_dict in all_failure_dicts:
            key = f"{f_dict['test_name']}:{f_dict['error_type']}"
            if key not in unique_failures:
                # Convert dict back to TestFailure
                unique_failures[key] = TestFailure(**{k: v for k, v in f_dict.items() if k in TestFailure.__annotations__})

        failures = list(unique_failures.values())

        # Attempt fixes
        if failures:
            fix_results = self.attempt_fixes(failures)
            iteration_data['fixes_applied'] = fix_results['applied']

            self.log(f"Fix summary: {len(fix_results['applied'])} applied, "
                    f"{len(fix_results['skipped'])} skipped, "
                    f"{len(fix_results['failed'])} failed", "INFO")
        else:
            self.log("No actionable failures found", "INFO")

        self.iteration_history.append(iteration_data)
        return False

    def run(self) -> bool:
        """Run the complete feedback loop."""
        self.log("Starting GAMMA Feedback Loop", "ITERATION")
        self.log(f"Max iterations: {self.max_iterations}", "INFO")
        self.log(f"Test command: {self.test_command}", "INFO")
        self.log(f"Auto-fix: {self.auto_fix}", "INFO")

        start_time = time.time()

        for iteration in range(1, self.max_iterations + 1):
            if self.run_iteration(iteration):
                elapsed = time.time() - start_time
                self.log("=" * 80, "SUCCESS")
                self.log(f"✅ ALL TESTS PASSED after {iteration} iteration(s)!", "SUCCESS")
                self.log(f"Time elapsed: {elapsed:.2f} seconds", "SUCCESS")
                self.log("=" * 80, "SUCCESS")
                self.save_summary(success=True)
                return True

            # Small delay between iterations
            if iteration < self.max_iterations:
                time.sleep(1)

        # Max iterations reached without success
        elapsed = time.time() - start_time
        self.log("=" * 80, "ERROR")
        self.log(f"❌ Tests still failing after {self.max_iterations} iterations", "ERROR")
        self.log(f"Total unique failures encountered: {len(self.all_failures)}", "ERROR")
        self.log(f"Time elapsed: {elapsed:.2f} seconds", "ERROR")
        self.log("=" * 80, "ERROR")
        self.save_summary(success=False)
        return False

    def save_summary(self, success: bool):
        """Save a summary of the feedback loop execution."""
        summary_file = ROOT_DIR / 'output' / f'feedback_loop_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        summary_file.parent.mkdir(exist_ok=True)

        summary = {
            'success': success,
            'iterations': len(self.iteration_history),
            'max_iterations': self.max_iterations,
            'unique_failures': list(self.all_failures),
            'history': self.iteration_history,
            'test_command': self.test_command,
            'auto_fix': self.auto_fix
        }

        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        self.log(f"Summary saved to: {summary_file}", "INFO")

    def __del__(self):
        """Cleanup."""
        if self.log_handle:
            self.log_handle.close()


def main():
    parser = argparse.ArgumentParser(
        description='GAMMA Feedback Loop - Automated Testing and Fixing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run tests only
  python tools/feedback_loop.py --verbose

  # Run live + tests with auto-fix
  python tools/feedback_loop.py --live --auto-fix --max-iterations 3

  # Run specific test filter
  python tools/feedback_loop.py --test-filter "test_engine"

  # Custom live modes
  python tools/feedback_loop.py --live --live-modes "game --help" "comparison --help"
        """
    )

    parser.add_argument('--max-iterations', type=int, default=5,
                       help='Maximum number of fix iterations (default: 5)')
    parser.add_argument('--test-command', default='./run_tests.sh',
                       help='Test command to run (default: ./run_tests.sh)')
    parser.add_argument('--auto-fix', action='store_true',
                       help='Automatically apply suggested fixes without prompting')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed output')
    parser.add_argument('--log-file',
                       help='Save detailed logs to file')
    parser.add_argument('--test-filter',
                       help='Only run tests matching this pattern (pytest -k)')
    parser.add_argument('--live', action='store_true',
                       help='Run live end-to-end execution of gamma.py')
    parser.add_argument('--live-modes', nargs='+',
                       help='Custom live modes to run (e.g., "game --help" "comparison --help")')
    parser.add_argument('--live-timeout', type=int, default=30,
                       help='Timeout for each live execution in seconds (default: 30)')

    args = parser.parse_args()

    # Create and run feedback loop
    loop = FeedbackLoop(
        max_iterations=args.max_iterations,
        test_command=args.test_command,
        auto_fix=args.auto_fix,
        verbose=args.verbose,
        log_file=args.log_file,
        test_filter=args.test_filter,
        run_live=args.live,
        live_modes=args.live_modes,
        live_timeout=args.live_timeout
    )

    success = loop.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
