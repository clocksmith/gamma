#!/usr/bin/env python3
"""
GAMMA Interactive Feedback Loop with Claude Code
Leverages Claude Code's capabilities to intelligently analyze and fix issues.

This script runs in a loop:
1. Executes tests and/or live gamma.py runs
2. Captures errors and context
3. Presents failures to Claude Code for analysis
4. Applies suggested fixes
5. Repeats until success

Usage:
    python tools/feedback_loop_interactive.py [options]

This script is designed to work WITH Claude Code, not standalone.
Run this in a Claude Code session to get intelligent assistance.
"""

import argparse
import subprocess
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    from tools._path_setup import ensure_project_root_on_path, ensure_src_on_path, ensure_tools_on_path
except ModuleNotFoundError:
    from _path_setup import ensure_project_root_on_path, ensure_src_on_path, ensure_tools_on_path

ROOT_DIR = Path(ensure_project_root_on_path())
ensure_src_on_path()
ensure_tools_on_path()

try:
    from tools.log_analyzer import LogAnalyzer, TestFailure
except ModuleNotFoundError:
    from log_analyzer import LogAnalyzer, TestFailure


@dataclass
class ExecutionResult:
    """Result of a test or live execution."""
    success: bool
    command: str
    stdout: str
    stderr: str
    exit_code: int
    duration: float
    failures: List[TestFailure]


class InteractiveFeedbackLoop:
    """
    Interactive feedback loop that presents failures to Claude Code.

    This class orchestrates the test-fix-retest cycle while providing
    structured information that Claude Code can use to diagnose and fix issues.
    """

    def __init__(self,
                 max_iterations: int = 10,
                 run_tests: bool = True,
                 run_live: bool = True,
                 test_command: str = "./run_tests.sh",
                 live_modes: Optional[List[str]] = None,
                 verbose: bool = True):

        self.max_iterations = max_iterations
        self.run_tests = run_tests
        self.run_live = run_live
        self.test_command = test_command
        self.live_modes = live_modes or ['game --help', 'comparison --help']
        self.verbose = verbose

        self.analyzer = LogAnalyzer()
        self.iteration = 0
        self.history = []

    def execute_command(self, command: str, timeout: int = 120, stdin: str = None) -> ExecutionResult:
        """Execute a command and capture results."""
        if self.verbose:
            print(f"\n▶ Executing: {command}")

        start_time = time.time()

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(ROOT_DIR),
                timeout=timeout,
                input=stdin
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            # Analyze failures
            combined_output = result.stdout + '\n' + result.stderr
            failures = self.analyzer.parse_test_output(combined_output)

            return ExecutionResult(
                success=success,
                command=command,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                duration=duration,
                failures=failures
            )

        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            return ExecutionResult(
                success=False,
                command=command,
                stdout=e.stdout.decode() if e.stdout else "",
                stderr=e.stderr.decode() if e.stderr else "",
                exit_code=-1,
                duration=duration,
                failures=[]
            )
        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                success=False,
                command=command,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                duration=duration,
                failures=[]
            )

    def run_iteration(self) -> bool:
        """Run one iteration and return True if all tests pass."""
        self.iteration += 1

        print("\n" + "=" * 80)
        print(f"ITERATION {self.iteration}/{self.max_iterations}")
        print("=" * 80)

        iteration_results = {
            'iteration': self.iteration,
            'timestamp': datetime.now().isoformat(),
            'executions': [],
            'all_passed': False
        }

        all_passed = True

        # Run live executions
        if self.run_live:
            print("\n📡 Running live end-to-end executions...")
            for mode in self.live_modes:
                cmd = f"python gamma.py {mode}"
                stdin = "\n/quit\nexit\n" if '--help' not in mode else None
                result = self.execute_command(cmd, timeout=30, stdin=stdin)

                iteration_results['executions'].append({
                    'type': 'live',
                    'mode': mode,
                    'success': result.success,
                    'duration': result.duration,
                    'failures': [f.to_dict() for f in result.failures]
                })

                if not result.success:
                    all_passed = False
                    print(f"  ✗ FAILED: {mode} (exit code: {result.exit_code})")
                    if result.failures:
                        print(f"    Found {len(result.failures)} error(s)")
                else:
                    print(f"  ✓ PASSED: {mode} ({result.duration:.2f}s)")

        # Run tests
        if self.run_tests:
            print("\n🧪 Running tests...")
            result = self.execute_command(self.test_command, timeout=300)

            iteration_results['executions'].append({
                'type': 'tests',
                'command': self.test_command,
                'success': result.success,
                'duration': result.duration,
                'failures': [f.to_dict() for f in result.failures]
            })

            if not result.success:
                all_passed = False
                print(f"  ✗ TESTS FAILED (exit code: {result.exit_code})")
                if result.failures:
                    print(f"    Found {len(result.failures)} failure(s)")
            else:
                print(f"  ✓ ALL TESTS PASSED ({result.duration:.2f}s)")

        iteration_results['all_passed'] = all_passed
        self.history.append(iteration_results)

        return all_passed

    def generate_failure_report(self) -> str:
        """Generate a detailed failure report for Claude Code to analyze."""
        if not self.history:
            return "No execution history available."

        latest = self.history[-1]

        report = []
        report.append("# GAMMA Feedback Loop - Failure Report")
        report.append(f"\nIteration: {latest['iteration']}")
        report.append(f"Timestamp: {latest['timestamp']}")
        report.append("\n" + "=" * 80)

        all_failures = []

        for execution in latest['executions']:
            exec_type = execution['type']
            success = execution['success']
            failures = execution['failures']

            if exec_type == 'live':
                mode = execution['mode']
                report.append(f"\n## Live Execution: gamma.py {mode}")
                report.append(f"Status: {'✓ PASSED' if success else '✗ FAILED'}")
                report.append(f"Duration: {execution['duration']:.2f}s")
            else:
                report.append(f"\n## Test Suite: {execution['command']}")
                report.append(f"Status: {'✓ PASSED' if success else '✗ FAILED'}")
                report.append(f"Duration: {execution['duration']:.2f}s")

            if failures:
                report.append(f"\n### Failures ({len(failures)}):")
                for i, failure in enumerate(failures, 1):
                    report.append(f"\n{i}. **{failure['test_name']}**")
                    report.append(f"   - Type: {failure['error_type']}")
                    report.append(f"   - Severity: {failure['severity']}")
                    report.append(f"   - Message: {failure['error_message'][:200]}")
                    if failure['file_path']:
                        report.append(f"   - Location: {failure['file_path']}:{failure['line_number']}")
                    if failure['traceback']:
                        report.append(f"   - Traceback snippet:")
                        tb_lines = failure['traceback'].split('\n')[:5]
                        for line in tb_lines:
                            report.append(f"     {line}")

                all_failures.extend(failures)

        # Summary
        report.append("\n" + "=" * 80)
        report.append(f"\n## Summary")
        report.append(f"Total failures: {len(all_failures)}")

        if all_failures:
            # Categorize by severity
            by_severity = {}
            for f in all_failures:
                sev = f['severity']
                by_severity.setdefault(sev, []).append(f)

            report.append("\nBy severity:")
            for severity in ['critical', 'high', 'medium', 'low']:
                if severity in by_severity:
                    report.append(f"  - {severity.upper()}: {len(by_severity[severity])}")

            # Most common error types
            by_type = {}
            for f in all_failures:
                err_type = f['error_type']
                by_type.setdefault(err_type, []).append(f)

            report.append("\nBy error type:")
            for err_type, failures in sorted(by_type.items(), key=lambda x: -len(x[1]))[:5]:
                report.append(f"  - {err_type}: {len(failures)}")

        report.append("\n" + "=" * 80)
        report.append("\n## Next Steps")
        report.append("\nClaude Code, please analyze these failures and suggest fixes.")
        report.append("For each failure, consider:")
        report.append("1. Root cause of the error")
        report.append("2. Files that need to be modified")
        report.append("3. Specific changes to make")
        report.append("4. Any dependencies or prerequisites")
        report.append("\nAfter suggesting fixes, you can apply them using the Edit or Write tools.")

        return '\n'.join(report)

    def save_report(self, report: str, filename: str = None):
        """Save failure report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"feedback_report_{timestamp}.md"

        output_dir = ROOT_DIR / 'output' / 'feedback_reports'
        output_dir.mkdir(parents=True, exist_ok=True)

        report_path = output_dir / filename
        with open(report_path, 'w') as f:
            f.write(report)

        return report_path

    def run(self):
        """Run the interactive feedback loop."""
        print("\n🚀 GAMMA Interactive Feedback Loop")
        print("=" * 80)
        print("This loop will run tests and live executions, then pause for fixes.")
        print(f"Max iterations: {self.max_iterations}")
        print(f"Run tests: {self.run_tests}")
        print(f"Run live: {self.run_live}")
        print("=" * 80)

        for _ in range(self.max_iterations):
            # Run iteration
            all_passed = self.run_iteration()

            if all_passed:
                print("\n" + "=" * 80)
                print("✅ SUCCESS! All tests and executions passed!")
                print("=" * 80)

                # Save success report
                report = self.generate_failure_report()
                report_path = self.save_report(report)
                print(f"\nReport saved: {report_path}")

                return True

            # Generate and display failure report
            print("\n" + "=" * 80)
            print("FAILURE ANALYSIS")
            print("=" * 80)

            report = self.generate_failure_report()
            print(report)

            # Save report
            report_path = self.save_report(report)
            print(f"\n📄 Full report saved to: {report_path}")

            # Pause for Claude Code to analyze and fix
            print("\n" + "=" * 80)
            print("⏸️  PAUSING FOR FIXES")
            print("=" * 80)
            print("\nClaude Code, please:")
            print("1. Review the failure report above")
            print("2. Analyze the errors and their root causes")
            print("3. Apply fixes using Edit/Write tools")
            print("4. When done, type 'continue' to proceed to next iteration")
            print("\nOr type 'abort' to stop the feedback loop.")
            print("=" * 80)

            # Wait for user input
            while True:
                response = input("\nEnter command (continue/abort): ").strip().lower()
                if response == 'continue':
                    print("\n▶ Continuing to next iteration...")
                    break
                elif response == 'abort':
                    print("\n⚠️  Feedback loop aborted by user")
                    return False
                else:
                    print("Invalid command. Please enter 'continue' or 'abort'")

        # Max iterations reached
        print("\n" + "=" * 80)
        print(f"⚠️  Maximum iterations ({self.max_iterations}) reached without success")
        print("=" * 80)

        return False


def main():
    parser = argparse.ArgumentParser(
        description='GAMMA Interactive Feedback Loop with Claude Code',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script is designed to work WITH Claude Code interactively.

The loop will:
1. Run tests and/or live gamma.py executions
2. Analyze failures and generate a detailed report
3. Pause and present failures to Claude Code
4. Wait for you (Claude Code) to apply fixes
5. Continue to next iteration

Example workflow:
1. Run: python tools/feedback_loop_interactive.py --live --max-iterations 5
2. Review the failure report
3. Apply fixes using Edit/Write tools
4. Type 'continue' to proceed
5. Repeat until all tests pass

Examples:
  # Run both tests and live executions
  python tools/feedback_loop_interactive.py --live

  # Run only tests
  python tools/feedback_loop_interactive.py --no-live

  # Custom live modes
  python tools/feedback_loop_interactive.py --live-modes "game --help" "game --version"
        """
    )

    parser.add_argument('--max-iterations', type=int, default=10,
                       help='Maximum number of iterations (default: 10)')
    parser.add_argument('--no-tests', action='store_true',
                       help='Skip running tests')
    parser.add_argument('--no-live', action='store_true',
                       help='Skip live executions')
    parser.add_argument('--test-command', default='./run_tests.sh',
                       help='Test command to run (default: ./run_tests.sh)')
    parser.add_argument('--live-modes', nargs='+',
                       help='Live modes to test (default: game --help, comparison --help)')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce output verbosity')

    args = parser.parse_args()

    loop = InteractiveFeedbackLoop(
        max_iterations=args.max_iterations,
        run_tests=not args.no_tests,
        run_live=not args.no_live,
        test_command=args.test_command,
        live_modes=args.live_modes,
        verbose=not args.quiet
    )

    success = loop.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
