"""Explicit safe test groups; never recursively discover historical result copies."""
import argparse
from pathlib import Path
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]
GROUPS = {
    "pure": ["architecture/test_closure.py", "architecture/test_primitives.py", "architecture/test_boundaries.py", "architecture/test_memory.py",
             "architecture/test_history.py", "architecture/test_original_inputs.py", "architecture/test_lease.py", "test_enwiki9_lab_recovery_activation.py",
             "test_enwiki9_lab_worker_liveness.py", "test_record_driver_result.py", "test_fx2_relational_terminal.py",
             "test_enwiki9_entry_resources.py", "test_enwiki9_ledger_navigation.py",
             "test_objective90_migration.py", "test_objective96_migration.py", "test_enwiki9_report_targets.py",
             "-m", "not historical"],
    "codec": ["architecture/test_migration.py", "test_enwiki9_predictor_driver.py", "test_raw_reverse_bz2_v1.py",
              "test_raw_reverse_bz2_gate_v1.py", "test_xml_history_deflate_v1.py",
              "test_xml_history_runtime_identity.py", "-m", "not native"],
    "native": ["architecture/test_migration.py", "test_fx2_title_memory_v1.py", "test_fx2_envelope.py", "test_causal_relational_v1.py", "test_causal_relational_v2.py", "test_causal_relational_integration.py"],
    "historical": ["architecture/test_history.py", "-m", "historical"],
    "linux": ["architecture/test_linux_resources.py", "architecture/test_lease.py"],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group", choices=GROUPS)
    args = parser.parse_args()
    selection = [str(PROJECT / "tests" / p) if p.endswith(".py") else p for p in GROUPS[args.group]]
    return subprocess.call([sys.executable, "-m", "pytest", "-q", *selection], cwd=PROJECT.parents[1])


if __name__ == "__main__":
    raise SystemExit(main())
