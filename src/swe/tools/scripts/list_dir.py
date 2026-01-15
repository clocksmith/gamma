"""List directory contents."""

from pathlib import Path


def execute(path: str = ".", pattern: str = "*", recursive: bool = False) -> dict:
    """
    List files in directory.

    Args:
        path: Directory path
        pattern: Glob pattern (e.g., "*.py")
        recursive: Whether to recurse into subdirectories

    Returns:
        dict with files and directories
    """
    try:
        dir_path = Path(path)
        if not dir_path.exists():
            return {"error": f"Path not found: {path}", "files": [], "dirs": []}

        if not dir_path.is_dir():
            return {"error": f"Not a directory: {path}", "files": [], "dirs": []}

        if recursive:
            matches = list(dir_path.rglob(pattern))
        else:
            matches = list(dir_path.glob(pattern))

        files = sorted([str(p.relative_to(dir_path)) for p in matches if p.is_file()])
        dirs = sorted([str(p.relative_to(dir_path)) for p in matches if p.is_dir()])

        return {
            "files": files[:100],  # Limit results
            "dirs": dirs[:50],
            "total_files": len(files),
            "total_dirs": len(dirs),
        }
    except Exception as e:
        return {"error": str(e), "files": [], "dirs": []}


execute.tool_info = {
    "tags": ["list", "dir", "filesystem"],
}
