"""Apply a git patch."""

import asyncio
import tempfile
import os


async def execute(patch: str, repo_path: str, check_only: bool = False) -> dict:
    """
    Apply a git patch to repository.

    Args:
        patch: Patch content (git diff format)
        repo_path: Path to repository
        check_only: If True, only check if patch applies

    Returns:
        dict with success status and modified files
    """
    # Write patch to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".patch", delete=False) as f:
        f.write(patch)
        patch_file = f.name

    try:
        cmd = ["git", "apply"]
        if check_only:
            cmd.append("--check")
        cmd.append(patch_file)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

        if proc.returncode == 0:
            # Extract modified files from patch
            files = []
            for line in patch.split("\n"):
                if line.startswith("diff --git"):
                    parts = line.split(" b/")
                    if len(parts) > 1:
                        files.append(parts[1])

            return {
                "success": True,
                "files_modified": files,
                "message": "Patch applied" if not check_only else "Patch valid",
            }
        else:
            error = stderr.decode()
            if "patch does not apply" in error.lower():
                return {"success": False, "error": "Patch conflicts", "details": error}
            return {"success": False, "error": error}

    except asyncio.TimeoutError:
        return {"success": False, "error": "Apply timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        os.unlink(patch_file)


execute.tool_info = {
    "tags": ["git", "apply", "patch", "edit"],
}
