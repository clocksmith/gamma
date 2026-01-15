"""Search for pattern in files."""

import subprocess
from pathlib import Path


def execute(pattern: str, path: str = ".", max_results: int = 50) -> dict:
    """
    Search for pattern in codebase using grep.

    Args:
        pattern: Regex pattern to search
        path: Directory to search in
        max_results: Maximum matches to return

    Returns:
        dict with matches and count
    """
    try:
        result = subprocess.run(
            ["grep", "-rn", "--include=*.py", pattern, path],
            capture_output=True,
            text=True,
            timeout=30,
        )

        lines = result.stdout.strip().split("\n") if result.stdout else []
        lines = [l for l in lines if l][:max_results]

        return {
            "matches": lines,
            "count": len(lines),
            "truncated": len(lines) == max_results,
        }
    except subprocess.TimeoutExpired:
        return {"error": "Search timed out", "matches": [], "count": 0}
    except Exception as e:
        return {"error": str(e), "matches": [], "count": 0}


execute.tool_info = {
    "tags": ["search", "grep", "text", "code"],
}
