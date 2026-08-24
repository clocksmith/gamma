#!/usr/bin/env python3
"""Materialize the v3 program lock while owning the managed lane namespace."""

from pathlib import Path

from managed_lane import OwnedNamespaceLock, argument_path, load_tool


PROJECT = Path(__file__).resolve().parents[2]


def main() -> int:
    lease = argument_path("--exclusive-lease")
    tool = load_tool(PROJECT, "gamma_mechanism_ir_program_lock_materialize.py", "gamma_ir_v3_lock_materializer_frozen")
    with OwnedNamespaceLock.acquire(lease) as guard:
        tool.require_clear_lease = guard.assert_owned
        return int(tool.main())


if __name__ == "__main__":
    raise SystemExit(main())
