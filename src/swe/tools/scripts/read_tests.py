"""List test files in a repository."""

import subprocess


def execute(path: str = ".", max_results: int = 200) -> dict:
    """
    List test files using ripgrep.

    Args:
        path: Directory to search
        max_results: Maximum files to return

    Returns:
        dict with test file paths and count
    """
    try:
        result = subprocess.run(
            [
                "rg",
                "--files",
                "-g", "*test*.py",
                "-g", "*tests*.py",
                "-g", "*test*.js",
                "-g", "*test*.ts",
                "-g", "*spec*.js",
                "-g", "*spec*.ts",
                path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        files = result.stdout.strip().split("\n") if result.stdout else []
        files = [f for f in files if f][:max_results]

        return {
            "tests": files,
            "count": len(files),
            "truncated": len(files) == max_results,
        }
    except FileNotFoundError:
        return {"error": "rg not installed", "tests": [], "count": 0}
    except subprocess.TimeoutExpired:
        return {"error": "Search timed out", "tests": [], "count": 0}
    except Exception as e:
        return {"error": str(e), "tests": [], "count": 0}


execute.tool_info = {
    "tags": ["tests", "discover", "qa", "repo"],
}
