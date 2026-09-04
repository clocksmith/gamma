"""Entry point for the zero-credit orphan-trace exact HORIZON replay."""

from pathlib import Path
import subprocess


PROJECT = Path(__file__).resolve().parents[2]
RUNNER = PROJECT / "tools/endpoint428_horizon_retained_parent_trace_exact_recovery_q0_v3.py"


def main() -> int:
    return subprocess.run(
        ["/usr/bin/python3", str(RUNNER)], cwd=PROJECT, check=False
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
