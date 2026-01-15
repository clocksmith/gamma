"""Clone a git repository at specific commit."""

import asyncio
import shutil
from pathlib import Path


async def execute(
    repo_url: str,
    commit: str,
    dest: str = "/tmp/swe-agent-v2/repo",
) -> dict:
    """
    Clone repository at specific commit.

    Args:
        repo_url: Git repository URL
        commit: Commit SHA to checkout
        dest: Destination path

    Returns:
        dict with success status and path
    """
    dest_path = Path(dest)

    # Clean existing
    if dest_path.exists():
        shutil.rmtree(dest_path)

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Clone
        proc = await asyncio.create_subprocess_exec(
            "git", "clone", "--depth", "1", repo_url, str(dest_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

        if proc.returncode != 0:
            return {"success": False, "error": stderr.decode(), "path": None}

        # Fetch commit
        proc = await asyncio.create_subprocess_exec(
            "git", "fetch", "--depth", "1", "origin", commit,
            cwd=str(dest_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=60)

        # Checkout
        proc = await asyncio.create_subprocess_exec(
            "git", "checkout", commit,
            cwd=str(dest_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

        if proc.returncode != 0:
            return {"success": False, "error": stderr.decode(), "path": str(dest_path)}

        return {"success": True, "path": str(dest_path), "commit": commit}

    except asyncio.TimeoutError:
        return {"success": False, "error": "Clone timed out", "path": None}
    except Exception as e:
        return {"success": False, "error": str(e), "path": None}


execute.tool_info = {
    "tags": ["git", "clone", "repo"],
}
