"""
Git tools for real git operations.

Provides clone, apply patch, diff generation, etc.
"""

import asyncio
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class ApplyStatus(Enum):
    """Status of patch application."""
    SUCCESS = "success"
    CONFLICT = "conflict"
    ERROR = "error"


@dataclass
class ApplyResult:
    """Result of applying a patch."""
    status: ApplyStatus
    message: str
    files_modified: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)


@dataclass
class CloneResult:
    """Result of cloning a repository."""
    success: bool
    path: str
    message: str
    commit_sha: Optional[str] = None


class GitTools:
    """
    Real git operations for SWE-bench tasks.

    Provides methods for:
    - Cloning repositories at specific commits
    - Applying patches
    - Generating diffs
    - Checking out commits
    """

    def __init__(self, work_dir: str = "/tmp/swe-agent"):
        """
        Initialize git tools.

        Args:
            work_dir: Base directory for cloned repositories
        """
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

    async def _run_command(
        self,
        cmd: List[str],
        cwd: Optional[str] = None,
        timeout: int = 300,
    ) -> tuple[int, str, str]:
        """
        Run a shell command asynchronously.

        Args:
            cmd: Command and arguments
            cwd: Working directory
            timeout: Timeout in seconds

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            return (
                process.returncode,
                stdout.decode("utf-8", errors="replace"),
                stderr.decode("utf-8", errors="replace"),
            )
        except asyncio.TimeoutError:
            process.kill()
            return -1, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return -1, "", str(e)

    async def clone(
        self,
        repo_url: str,
        commit: str,
        dest_name: Optional[str] = None,
    ) -> CloneResult:
        """
        Clone a repository at a specific commit.

        Args:
            repo_url: Git repository URL
            commit: Commit SHA to checkout
            dest_name: Optional destination directory name

        Returns:
            CloneResult with status and path
        """
        if dest_name is None:
            # Extract repo name from URL
            dest_name = repo_url.rstrip("/").split("/")[-1]
            if dest_name.endswith(".git"):
                dest_name = dest_name[:-4]
            dest_name = f"{dest_name}_{commit[:8]}"

        dest_path = self.work_dir / dest_name

        # Remove existing directory if present
        if dest_path.exists():
            import shutil
            shutil.rmtree(dest_path)

        # Clone the repository
        rc, stdout, stderr = await self._run_command([
            "git", "clone", "--depth", "1", repo_url, str(dest_path)
        ])

        if rc != 0:
            return CloneResult(
                success=False,
                path=str(dest_path),
                message=f"Clone failed: {stderr}",
            )

        # Fetch the specific commit
        rc, stdout, stderr = await self._run_command([
            "git", "fetch", "--depth", "1", "origin", commit
        ], cwd=str(dest_path))

        if rc != 0:
            return CloneResult(
                success=False,
                path=str(dest_path),
                message=f"Fetch commit failed: {stderr}",
            )

        # Checkout the commit
        rc, stdout, stderr = await self._run_command([
            "git", "checkout", commit
        ], cwd=str(dest_path))

        if rc != 0:
            return CloneResult(
                success=False,
                path=str(dest_path),
                message=f"Checkout failed: {stderr}",
            )

        return CloneResult(
            success=True,
            path=str(dest_path),
            message="Clone successful",
            commit_sha=commit,
        )

    async def apply_patch(
        self,
        patch: str,
        repo_path: str,
        check_only: bool = False,
    ) -> ApplyResult:
        """
        Apply a git patch to a repository.

        Args:
            patch: The patch content (git diff format)
            repo_path: Path to the repository
            check_only: If True, only check if patch applies (--check)

        Returns:
            ApplyResult with status and details
        """
        # Write patch to temp file
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".patch",
            delete=False,
        ) as f:
            f.write(patch)
            patch_file = f.name

        try:
            cmd = ["git", "apply"]
            if check_only:
                cmd.append("--check")
            cmd.append(patch_file)

            rc, stdout, stderr = await self._run_command(
                cmd,
                cwd=repo_path,
            )

            if rc == 0:
                # Get list of modified files
                files = []
                for line in patch.split("\n"):
                    if line.startswith("diff --git"):
                        parts = line.split(" b/")
                        if len(parts) > 1:
                            files.append(parts[1])

                return ApplyResult(
                    status=ApplyStatus.SUCCESS,
                    message="Patch applied successfully" if not check_only else "Patch can be applied",
                    files_modified=files,
                )
            elif "patch does not apply" in stderr.lower():
                return ApplyResult(
                    status=ApplyStatus.CONFLICT,
                    message=f"Patch conflicts: {stderr}",
                )
            else:
                return ApplyResult(
                    status=ApplyStatus.ERROR,
                    message=f"Patch failed: {stderr}",
                )
        finally:
            os.unlink(patch_file)

    async def generate_diff(
        self,
        repo_path: str,
        staged_only: bool = False,
    ) -> str:
        """
        Generate a diff of current changes.

        Args:
            repo_path: Path to the repository
            staged_only: If True, only show staged changes

        Returns:
            Git diff output
        """
        cmd = ["git", "diff"]
        if staged_only:
            cmd.append("--staged")

        rc, stdout, stderr = await self._run_command(cmd, cwd=repo_path)

        if rc != 0:
            raise RuntimeError(f"Git diff failed: {stderr}")

        return stdout

    async def get_current_commit(self, repo_path: str) -> str:
        """Get the current commit SHA."""
        rc, stdout, stderr = await self._run_command(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
        )

        if rc != 0:
            raise RuntimeError(f"Git rev-parse failed: {stderr}")

        return stdout.strip()

    async def reset_hard(self, repo_path: str, commit: str = "HEAD") -> bool:
        """Reset repository to a specific commit."""
        rc, stdout, stderr = await self._run_command(
            ["git", "reset", "--hard", commit],
            cwd=repo_path,
        )
        return rc == 0

    async def clean(self, repo_path: str) -> bool:
        """Clean untracked files from repository."""
        rc, stdout, stderr = await self._run_command(
            ["git", "clean", "-fd"],
            cwd=repo_path,
        )
        return rc == 0
