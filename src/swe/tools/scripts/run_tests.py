"""Run tests."""

import subprocess


def execute(path: str = ".", test_filter: str = None, timeout: int = 60) -> dict:
    """
    Run pytest on the codebase.

    Args:
        path: Path to test directory or file
        test_filter: Optional test name filter (-k flag)
        timeout: Timeout in seconds

    Returns:
        dict with pass/fail counts and output
    """
    try:
        cmd = ["python", "-m", "pytest", path, "-v", "--tb=short"]
        if test_filter:
            cmd.extend(["-k", test_filter])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        output = result.stdout + result.stderr

        # Parse results
        passed = output.count(" PASSED")
        failed = output.count(" FAILED")
        errors = output.count(" ERROR")

        return {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "success": failed == 0 and errors == 0,
            "output": output[-2000:] if len(output) > 2000 else output,
            "return_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "error": f"Tests timed out after {timeout}s",
            "passed": 0,
            "failed": 0,
            "success": False,
        }
    except Exception as e:
        return {"error": str(e), "passed": 0, "failed": 0, "success": False}


execute.tool_info = {
    "tags": ["test", "pytest", "qa"],
}
