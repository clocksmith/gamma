"""Get git blame for a file range."""

import subprocess
from pathlib import Path


def execute(path: str, start_line: int = 1, line_count: int = 20, repo_path: str = ".") -> dict:
    """
    Run git blame for a file line range.

    Args:
        path: File path relative to repo
        start_line: 1-based start line
        line_count: Number of lines to blame
        repo_path: Repository root path

    Returns:
        dict with blame output and status
    """
    try:
        file_path = Path(repo_path) / path
        if not file_path.exists():
            return {"error": f"File not found: {path}", "blame": None}

        end_line = max(start_line, start_line + line_count - 1)
        result = subprocess.run(
            ["git", "blame", "-L", f"{start_line},{end_line}", path],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return {"error": result.stderr.strip(), "blame": None}

        return {
            "blame": result.stdout.strip().split("\n"),
            "start_line": start_line,
            "end_line": end_line,
        }
    except subprocess.TimeoutExpired:
        return {"error": "Blame timed out", "blame": None}
    except Exception as e:
        return {"error": str(e), "blame": None}


execute.tool_info = {
    "tags": ["git", "blame", "history", "lineage"],
}
