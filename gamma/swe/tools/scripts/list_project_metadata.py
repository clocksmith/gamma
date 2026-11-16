"""List common project metadata files."""

from pathlib import Path


def execute(path: str = ".") -> dict:
    """
    Read small snippets of common project metadata files.

    Args:
        path: Project root path

    Returns:
        dict with file presence and previews
    """
    root = Path(path)
    candidates = [
        "pyproject.toml",
        "setup.cfg",
        "setup.py",
        "requirements.txt",
        "package.json",
        "Cargo.toml",
        "go.mod",
        "README.md",
    ]

    results = {}
    for name in candidates:
        file_path = root / name
        if not file_path.exists():
            continue
        if not file_path.is_file():
            continue
        try:
            text = file_path.read_text(errors="ignore")
            preview = "\n".join(text.splitlines()[:40])
            results[name] = {
                "path": str(file_path),
                "preview": preview,
                "lines": len(text.splitlines()),
            }
        except Exception as e:
            results[name] = {"error": str(e)}

    return {
        "files": results,
        "count": len(results),
    }


execute.tool_info = {
    "tags": ["metadata", "project", "repo", "config"],
}
