#!/usr/bin/env python3
"""Run the unchanged Mechanism IR v3 compiler under the managed lane lock."""

from pathlib import Path

from managed_lane import (
    BorrowedNamespaceLock,
    OwnedNamespaceLock,
    argument_path,
    load_tool,
)


PROJECT = Path(__file__).resolve().parents[2]


def main() -> int:
    lease = argument_path("--exclusive-lease")
    tool = load_tool(PROJECT, "gamma_mechanism_ir_compile_v2.py", "gamma_ir_v3_compiler_frozen")
    borrowed = BorrowedNamespaceLock.from_environment(lease)
    if borrowed is not None:
        try:
            tool.require_lease_clear = borrowed.assert_owned
            return_code = int(tool.main())
            borrowed.assert_owned(lease)
            return return_code
        finally:
            borrowed.close()
    with OwnedNamespaceLock.acquire(lease) as guard:
        tool.require_lease_clear = guard.assert_owned
        return int(tool.main())


if __name__ == "__main__":
    raise SystemExit(main())
