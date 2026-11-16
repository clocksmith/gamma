"""Search for pattern with surrounding context using ripgrep."""

import subprocess


def execute(pattern: str, path: str = ".", context: int = 2, max_results: int = 200) -> dict:
    """
    Search for pattern with context lines.

    Args:
        pattern: Regex pattern to search
        path: Directory to search in
        context: Number of context lines before/after
        max_results: Maximum lines to return

    Returns:
        dict with matches and count
    """
    try:
        result = subprocess.run(
            ["rg", "-n", "-C", str(context), pattern, path],
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
    except FileNotFoundError:
        return {"error": "rg not installed", "matches": [], "count": 0}
    except subprocess.TimeoutExpired:
        return {"error": "Search timed out", "matches": [], "count": 0}
    except Exception as e:
        return {"error": str(e), "matches": [], "count": 0}


execute.tool_info = {
    "tags": ["search", "rg", "context", "code"],
}
