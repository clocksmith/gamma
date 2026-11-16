"""Generate git diff of current changes."""

import asyncio


async def execute(repo_path: str, staged_only: bool = False) -> dict:
    """
    Generate diff of current changes.

    Args:
        repo_path: Path to repository
        staged_only: Only show staged changes

    Returns:
        dict with diff content
    """
    cmd = ["git", "diff"]
    if staged_only:
        cmd.append("--staged")

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

        if proc.returncode == 0:
            diff = stdout.decode()
            # Count changed files
            files = [l.split(" b/")[1] for l in diff.split("\n")
                     if l.startswith("diff --git") and " b/" in l]
            return {
                "diff": diff,
                "files_changed": files,
                "num_files": len(files),
                "has_changes": len(diff.strip()) > 0,
            }
        else:
            return {"error": stderr.decode(), "diff": None}

    except asyncio.TimeoutError:
        return {"error": "Diff timed out", "diff": None}
    except Exception as e:
        return {"error": str(e), "diff": None}


execute.tool_info = {
    "tags": ["git", "diff", "patch"],
}
