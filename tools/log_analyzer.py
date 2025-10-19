#!/usr/bin/env python3
"""
Log Analyzer for GAMMA Feedback Loop
Parses test output and identifies failures with context.
"""

import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class TestFailure:
    """Represents a single test failure with context."""
    test_name: str
    error_type: str  # ImportError, AssertionError, etc.
    error_message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    traceback: Optional[str] = None
    context_lines: Optional[List[str]] = None
    severity: str = "medium"  # low, medium, high, critical

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class LogAnalyzer:
    """Analyzes test output to identify and categorize failures."""

    # Common error patterns
    ERROR_PATTERNS = {
        'import_error': re.compile(r"(ImportError|ModuleNotFoundError): (.+)"),
        'attribute_error': re.compile(r"AttributeError: (.+)"),
        'assertion_error': re.compile(r"AssertionError: (.+)"),
        'type_error': re.compile(r"TypeError: (.+)"),
        'value_error': re.compile(r"ValueError: (.+)"),
        'name_error': re.compile(r"NameError: (.+)"),
        'syntax_error': re.compile(r"SyntaxError: (.+)"),
        'index_error': re.compile(r"IndexError: (.+)"),
        'key_error': re.compile(r"KeyError: (.+)"),
        'file_not_found': re.compile(r"FileNotFoundError: (.+)"),
    }

    # File and line number pattern
    FILE_LINE_PATTERN = re.compile(r'File "([^"]+)", line (\d+)')

    # Test name patterns
    PYTEST_FAILURE_PATTERN = re.compile(r"FAILED (.+?)::(test_\w+)")
    UNITTEST_FAILURE_PATTERN = re.compile(r"FAIL: (test_\w+)")

    def __init__(self):
        self.failures = []

    def parse_test_output(self, output: str) -> List[TestFailure]:
        """
        Parse test output and extract failures.

        Supports:
        - pytest output
        - unittest output
        - shell script test output (run_tests.sh format)
        """
        self.failures = []

        # Split into lines for processing
        lines = output.split('\n')

        # Try different parsing strategies
        self._parse_pytest_output(lines)
        self._parse_shell_script_output(lines)
        self._parse_python_traceback(output)

        # Deduplicate failures by test name + error type
        unique_failures = {}
        for failure in self.failures:
            key = f"{failure.test_name}:{failure.error_type}"
            if key not in unique_failures:
                unique_failures[key] = failure

        return list(unique_failures.values())

    def _parse_pytest_output(self, lines: List[str]):
        """Parse pytest-style output."""
        i = 0
        while i < len(lines):
            line = lines[i]

            # Look for FAILED test
            match = self.PYTEST_FAILURE_PATTERN.search(line)
            if match:
                test_file = match.group(1)
                test_name = match.group(2)

                # Collect error info from following lines
                error_type = "Unknown"
                error_message = ""
                traceback_lines = []

                # Look ahead for error details
                j = i + 1
                while j < len(lines) and j < i + 50:  # Look up to 50 lines ahead
                    next_line = lines[j]

                    # Check for error type
                    for err_name, pattern in self.ERROR_PATTERNS.items():
                        err_match = pattern.search(next_line)
                        if err_match:
                            error_type = err_name.replace('_', ' ').title()
                            error_message = err_match.group(1) if err_match.groups() else next_line
                            break

                    # Collect traceback
                    if next_line.strip().startswith('File ') or 'Traceback' in next_line:
                        traceback_lines.append(next_line)

                    # Stop at next test or separator
                    if next_line.startswith('FAILED ') or next_line.startswith('===='):
                        break

                    j += 1

                # Extract file and line number from traceback
                file_path = None
                line_number = None
                if traceback_lines:
                    for tb_line in reversed(traceback_lines):
                        file_match = self.FILE_LINE_PATTERN.search(tb_line)
                        if file_match:
                            file_path = file_match.group(1)
                            line_number = int(file_match.group(2))
                            break

                failure = TestFailure(
                    test_name=test_name,
                    error_type=error_type,
                    error_message=error_message[:500],  # Limit message length
                    file_path=file_path,
                    line_number=line_number,
                    traceback='\n'.join(traceback_lines[:20]),  # Limit traceback
                    severity=self._determine_severity(error_type)
                )
                self.failures.append(failure)

            i += 1

    def _parse_shell_script_output(self, lines: List[str]):
        """Parse run_tests.sh style output."""
        current_test = None

        for line in lines:
            # Look for test name
            if line.startswith("Test: "):
                current_test = line.replace("Test: ", "").strip()

            # Look for failure marker
            if "FAILED" in line and current_test:
                # Try to extract error from previous lines
                failure = TestFailure(
                    test_name=current_test,
                    error_type="Test Failed",
                    error_message=f"Test {current_test} failed",
                    severity="medium"
                )
                self.failures.append(failure)
                current_test = None

    def _parse_python_traceback(self, output: str):
        """Parse Python tracebacks from output."""
        # Split on Traceback markers
        tracebacks = re.split(r'Traceback \(most recent call last\):', output)

        for i, tb in enumerate(tracebacks[1:], 1):  # Skip first split (before first traceback)
            lines = tb.split('\n')

            # Extract file and line info
            file_path = None
            line_number = None
            for line in lines:
                file_match = self.FILE_LINE_PATTERN.search(line)
                if file_match:
                    file_path = file_match.group(1)
                    line_number = int(file_match.group(2))

            # Extract error type and message
            error_type = "Unknown Error"
            error_message = ""
            for line in reversed(lines[:20]):  # Check last 20 lines
                for err_name, pattern in self.ERROR_PATTERNS.items():
                    match = pattern.search(line)
                    if match:
                        error_type = err_name.replace('_', ' ').title()
                        error_message = match.group(1) if match.groups() else line.strip()
                        break
                if error_message:
                    break

            # Create failure if we found meaningful info
            if error_message or file_path:
                # Try to extract test name
                test_name = f"Traceback_{i}"
                for line in lines:
                    if 'test_' in line:
                        test_match = re.search(r'(test_\w+)', line)
                        if test_match:
                            test_name = test_match.group(1)
                            break

                failure = TestFailure(
                    test_name=test_name,
                    error_type=error_type,
                    error_message=error_message[:500],
                    file_path=file_path,
                    line_number=line_number,
                    traceback='\n'.join(lines[:30]),
                    severity=self._determine_severity(error_type)
                )

                # Only add if not duplicate
                is_duplicate = False
                for existing in self.failures:
                    if (existing.error_type == failure.error_type and
                        existing.error_message == failure.error_message):
                        is_duplicate = True
                        break

                if not is_duplicate:
                    self.failures.append(failure)

    def _determine_severity(self, error_type: str) -> str:
        """Determine severity based on error type."""
        critical_errors = ['Syntax Error', 'Import Error', 'Module Not Found Error']
        high_errors = ['Name Error', 'Attribute Error', 'Type Error']
        medium_errors = ['Assertion Error', 'Value Error']

        error_type_clean = error_type.replace('_', ' ').title()

        if error_type_clean in critical_errors:
            return "critical"
        elif error_type_clean in high_errors:
            return "high"
        elif error_type_clean in medium_errors:
            return "medium"
        else:
            return "low"

    def categorize_failures(self, failures: List[TestFailure]) -> Dict[str, List[TestFailure]]:
        """Categorize failures by type."""
        categories = {}

        for failure in failures:
            error_type = failure.error_type
            if error_type not in categories:
                categories[error_type] = []
            categories[error_type].append(failure)

        return categories

    def get_priority_failures(self, failures: List[TestFailure]) -> List[TestFailure]:
        """Get failures sorted by priority (severity)."""
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}

        return sorted(
            failures,
            key=lambda f: (severity_order.get(f.severity, 4), f.test_name)
        )


def main():
    """Demo/testing of log analyzer."""
    import sys

    if len(sys.argv) > 1:
        log_file = sys.argv[1]
        with open(log_file, 'r') as f:
            output = f.read()
    else:
        # Demo with sample output
        output = """
FAILED tests/test_example.py::test_something - ImportError: No module named 'foo'
  File "tests/test_example.py", line 10, in test_something
    import foo
FAILED tests/test_another.py::test_calculation - AssertionError: 5 != 4
  File "tests/test_another.py", line 25, in test_calculation
    assert result == 5
        """

    analyzer = LogAnalyzer()
    failures = analyzer.parse_test_output(output)

    print(f"Found {len(failures)} failure(s):\n")
    for i, failure in enumerate(failures, 1):
        print(f"{i}. {failure.test_name}")
        print(f"   Type: {failure.error_type} (Severity: {failure.severity})")
        print(f"   Message: {failure.error_message}")
        if failure.file_path:
            print(f"   Location: {failure.file_path}:{failure.line_number}")
        print()


if __name__ == '__main__':
    main()
