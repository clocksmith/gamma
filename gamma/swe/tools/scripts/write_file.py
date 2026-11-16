"""Write content to a file."""

from pathlib import Path


def execute(path: str, content: str, create_dirs: bool = True) -> dict:
    """
    Write content to a file.

    Args:
        path: Path to file
        content: Content to write
        create_dirs: Create parent directories if needed

    Returns:
        dict with success status
    """
    try:
        file_path = Path(path)

        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(content)

        return {
            "success": True,
            "path": str(file_path),
            "bytes_written": len(content),
            "lines": content.count("\n") + 1,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


execute.tool_info = {
    "tags": ["write", "file", "edit"],
}
