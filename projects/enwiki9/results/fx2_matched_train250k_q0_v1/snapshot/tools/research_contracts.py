#!/usr/bin/env python3
"""Compatibility validation entrance. Historical bytes resolve by closure ID."""
import sys
try:
    from . import _enwiki9_bootstrap
except ImportError:
    import _enwiki9_bootstrap
from gamma_enwiki9.evidence import contracts as _implementation
from gamma_enwiki9.reporting.driver_rows import build_driver_run_ledger_row as _build_row


def build_driver_run_ledger_row(result, result_path, *, program_name, recorded_utc=None):
    return _build_row(result, result_path, program_name=program_name, recorded_utc=recorded_utc,
        project_root=_implementation.PROJECT_ROOT, validate_row=_implementation.validate_driver_run_ledger_row)


# Preserve the legacy combined surface only at this compatibility boundary.
_implementation.build_driver_run_ledger_row = build_driver_run_ledger_row
if __name__ == "__main__":
    raise SystemExit(_implementation.main())
sys.modules[__name__] = _implementation
