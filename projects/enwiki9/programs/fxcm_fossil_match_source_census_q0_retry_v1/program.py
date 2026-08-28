"""Entry point for the zero-credit parent-independent FOSSIL census."""

from pathlib import Path
import subprocess


PROJECT = Path(__file__).resolve().parents[2]
RUNNER = PROJECT / "tools/fxcm_fossil_match_source_census_q0_retry_v1.py"


def main() -> int:
    return subprocess.run(
        ["/usr/bin/python3", str(RUNNER)],
        cwd=PROJECT,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
