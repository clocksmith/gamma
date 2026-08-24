#!/usr/bin/env python3
"""Repeat v3 compilation while retaining one canonical managed-lane lock."""

import os
from pathlib import Path

from managed_lane import OwnedNamespaceLock, argument_path, load_tool, validate_namespace


PROJECT = Path(__file__).resolve().parents[2]


def main() -> int:
    lease_argument = argument_path("--exclusive-lease")
    tool = load_tool(PROJECT, "gamma_mechanism_ir_compile_v2_verify.py", "gamma_ir_v3_compile_verifier_frozen")
    with OwnedNamespaceLock.acquire(lease_argument) as guard:
        lease, _ = validate_namespace(lease_argument)
        original_regular_file = tool.regular_file
        original_subprocess_run = tool.subprocess.run

        def regular_file(path: Path, label: str) -> Path:
            candidate, _ = validate_namespace(path)
            if label == "exclusive lease" and candidate == lease:
                guard.assert_owned(path)
                return candidate
            return original_regular_file(path, label)

        def inherited_subprocess_run(*args, **kwargs):
            environment = dict(kwargs.get("env") or os.environ)
            environment.update(guard.child_environment())
            kwargs["env"] = environment
            inherited = set(kwargs.get("pass_fds", ()))
            inherited.update(guard.child_descriptors())
            kwargs["pass_fds"] = tuple(sorted(inherited))
            return original_subprocess_run(*args, **kwargs)

        tool.regular_file = regular_file
        tool.subprocess.run = inherited_subprocess_run
        try:
            return_code = int(tool.main())
            guard.assert_owned(lease_argument)
            return return_code
        finally:
            tool.regular_file = original_regular_file
            tool.subprocess.run = original_subprocess_run


if __name__ == "__main__":
    raise SystemExit(main())
