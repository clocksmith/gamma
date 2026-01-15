"""Read file contents."""

from pathlib import Path


def execute(path: str, start_line: int = 0, max_lines: int = 200) -> dict:
    """
    Read contents of a file.

    Args:
        path: Path to file
        start_line: Line to start from (0-indexed)
        max_lines: Maximum lines to return

    Returns:
        dict with content and metadata
    """
    try:
        file_path = Path(path)
        if not file_path.exists():
            return {"error": f"File not found: {path}", "content": None}

        if not file_path.is_file():
            return {"error": f"Not a file: {path}", "content": None}

        content = file_path.read_text()
        lines = content.split("\n")
        total_lines = len(lines)

        # Slice to requested range
        selected = lines[start_line:start_line + max_lines]

        return {
            "content": "\n".join(selected),
            "total_lines": total_lines,
            "start_line": start_line,
            "lines_returned": len(selected),
            "truncated": start_line + max_lines < total_lines,
        }
    except Exception as e:
        return {"error": str(e), "content": None}


execute.tool_info = {
    "tags": ["read", "file", "code"],
}
