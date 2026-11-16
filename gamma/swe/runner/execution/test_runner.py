"""
Test runner for executing tests in repositories.

Supports pytest, Django tests, and auto-detection.
"""

import asyncio
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class TestStatus(Enum):
    """Status of a test run."""
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class TestCase:
    """Individual test case result."""
    name: str
    status: TestStatus
    duration_ms: int = 0
    error_message: Optional[str] = None
    traceback: Optional[str] = None


@dataclass
class TestResult:
    """Result of a test run."""
    status: TestStatus
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    total: int = 0
    duration_ms: int = 0
    test_cases: List[TestCase] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    error_message: Optional[str] = None

    @property
    def all_passed(self) -> bool:
        """Check if all tests passed."""
        return self.failed == 0 and self.errors == 0

    @property
    def success_rate(self) -> float:
        """Get success rate."""
        if self.total == 0:
            return 0.0
        return self.passed / self.total


class TestRunner:
    """
    Test runner for SWE-bench tasks.

    Supports:
    - pytest
    - Django test runner
    - Auto-detection of test framework
    """

    def __init__(self, timeout_seconds: int = 300):
        """
        Initialize test runner.

        Args:
            timeout_seconds: Default timeout for test runs
        """
        self.timeout_seconds = timeout_seconds

    async def _run_command(
        self,
        cmd: List[str],
        cwd: str,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> tuple[int, str, str]:
        """Run a shell command asynchronously."""
        timeout = timeout or self.timeout_seconds

        # Merge environment
        full_env = os.environ.copy()
        if env:
            full_env.update(env)

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=full_env,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            return (
                process.returncode,
                stdout.decode("utf-8", errors="replace"),
                stderr.decode("utf-8", errors="replace"),
            )
        except asyncio.TimeoutError:
            process.kill()
            return -1, "", f"Test run timed out after {timeout}s"
        except Exception as e:
            return -1, "", str(e)

    async def detect_test_framework(self, repo_path: str) -> str:
        """
        Detect the test framework used in a repository.

        Args:
            repo_path: Path to the repository

        Returns:
            Framework name: "pytest", "django", "unittest", or "unknown"
        """
        repo = Path(repo_path)

        # Check for pytest
        if (repo / "pytest.ini").exists() or (repo / "pyproject.toml").exists():
            pyproject = repo / "pyproject.toml"
            if pyproject.exists():
                content = pyproject.read_text()
                if "[tool.pytest" in content:
                    return "pytest"

        if (repo / "setup.cfg").exists():
            content = (repo / "setup.cfg").read_text()
            if "[tool:pytest]" in content:
                return "pytest"

        # Check for Django
        if (repo / "manage.py").exists():
            manage_content = (repo / "manage.py").read_text()
            if "django" in manage_content.lower():
                return "django"

        # Check for conftest.py (pytest)
        if list(repo.rglob("conftest.py")):
            return "pytest"

        # Default to pytest if tests directory exists
        if (repo / "tests").exists() or (repo / "test").exists():
            return "pytest"

        return "unknown"

    async def run_pytest(
        self,
        repo_path: str,
        test_files: Optional[List[str]] = None,
        markers: Optional[List[str]] = None,
        extra_args: Optional[List[str]] = None,
    ) -> TestResult:
        """
        Run pytest on a repository.

        Args:
            repo_path: Path to the repository
            test_files: Specific test files/directories to run
            markers: Pytest markers to filter tests
            extra_args: Additional pytest arguments

        Returns:
            TestResult with details
        """
        cmd = ["python", "-m", "pytest", "-v", "--tb=short"]

        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])

        if extra_args:
            cmd.extend(extra_args)

        if test_files:
            cmd.extend(test_files)

        rc, stdout, stderr = await self._run_command(cmd, cwd=repo_path)

        return self._parse_pytest_output(rc, stdout, stderr)

    def _parse_pytest_output(
        self,
        rc: int,
        stdout: str,
        stderr: str,
    ) -> TestResult:
        """Parse pytest output into TestResult."""
        test_cases = []
        passed = 0
        failed = 0
        errors = 0
        skipped = 0

        # Parse test results from output
        # Format: "test_file.py::test_name PASSED/FAILED/ERROR/SKIPPED"
        test_pattern = re.compile(
            r"^([\w/\.]+::\w+)\s+(PASSED|FAILED|ERROR|SKIPPED)",
            re.MULTILINE,
        )

        for match in test_pattern.finditer(stdout):
            name = match.group(1)
            status_str = match.group(2)

            status_map = {
                "PASSED": TestStatus.PASSED,
                "FAILED": TestStatus.FAILED,
                "ERROR": TestStatus.ERROR,
                "SKIPPED": TestStatus.SKIPPED,
            }
            status = status_map.get(status_str, TestStatus.ERROR)

            test_cases.append(TestCase(name=name, status=status))

            if status == TestStatus.PASSED:
                passed += 1
            elif status == TestStatus.FAILED:
                failed += 1
            elif status == TestStatus.ERROR:
                errors += 1
            elif status == TestStatus.SKIPPED:
                skipped += 1

        # Parse summary line
        summary_pattern = re.compile(
            r"(\d+) passed.*?(\d+) failed|(\d+) passed|(\d+) failed"
        )
        summary_match = summary_pattern.search(stdout)
        if summary_match and not test_cases:
            # Use summary if we couldn't parse individual tests
            groups = summary_match.groups()
            if groups[0] and groups[1]:
                passed = int(groups[0])
                failed = int(groups[1])
            elif groups[2]:
                passed = int(groups[2])
            elif groups[3]:
                failed = int(groups[3])

        total = passed + failed + errors + skipped

        # Determine overall status
        if rc == -1:
            status = TestStatus.TIMEOUT
        elif rc != 0 or failed > 0 or errors > 0:
            status = TestStatus.FAILED
        else:
            status = TestStatus.PASSED

        return TestResult(
            status=status,
            passed=passed,
            failed=failed,
            errors=errors,
            skipped=skipped,
            total=total,
            test_cases=test_cases,
            stdout=stdout,
            stderr=stderr,
        )

    async def run_django_tests(
        self,
        repo_path: str,
        apps: Optional[List[str]] = None,
        test_labels: Optional[List[str]] = None,
    ) -> TestResult:
        """
        Run Django tests on a repository.

        Args:
            repo_path: Path to the repository
            apps: Specific Django apps to test
            test_labels: Specific test labels to run

        Returns:
            TestResult with details
        """
        cmd = ["python", "manage.py", "test", "--verbosity=2"]

        if apps:
            cmd.extend(apps)

        if test_labels:
            cmd.extend(test_labels)

        rc, stdout, stderr = await self._run_command(cmd, cwd=repo_path)

        return self._parse_django_output(rc, stdout, stderr)

    def _parse_django_output(
        self,
        rc: int,
        stdout: str,
        stderr: str,
    ) -> TestResult:
        """Parse Django test output into TestResult."""
        passed = 0
        failed = 0
        errors = 0

        # Django outputs "OK" or "FAILED (failures=N, errors=M)"
        if "OK" in stdout:
            # Count dots for passed tests
            passed = stdout.count(".")

        fail_match = re.search(r"failures=(\d+)", stdout)
        error_match = re.search(r"errors=(\d+)", stdout)

        if fail_match:
            failed = int(fail_match.group(1))
        if error_match:
            errors = int(error_match.group(1))

        # Count test methods run
        run_match = re.search(r"Ran (\d+) test", stdout)
        total = int(run_match.group(1)) if run_match else passed + failed + errors

        # Determine overall status
        if rc == -1:
            status = TestStatus.TIMEOUT
        elif rc != 0 or failed > 0 or errors > 0:
            status = TestStatus.FAILED
        else:
            status = TestStatus.PASSED

        return TestResult(
            status=status,
            passed=passed,
            failed=failed,
            errors=errors,
            total=total,
            stdout=stdout,
            stderr=stderr,
        )

    async def run(
        self,
        repo_path: str,
        test_files: Optional[List[str]] = None,
    ) -> TestResult:
        """
        Run tests using auto-detected framework.

        Args:
            repo_path: Path to the repository
            test_files: Optional specific test files to run

        Returns:
            TestResult with details
        """
        framework = await self.detect_test_framework(repo_path)

        if framework == "django":
            return await self.run_django_tests(repo_path)
        elif framework in ("pytest", "unknown"):
            return await self.run_pytest(repo_path, test_files)
        else:
            return TestResult(
                status=TestStatus.ERROR,
                error_message=f"Unknown test framework: {framework}",
            )
