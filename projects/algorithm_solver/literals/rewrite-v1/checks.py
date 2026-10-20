"""Reuse the frozen scale-v2 development oracle; no new expected answers."""
import importlib.util
from pathlib import Path
path=Path(__file__).resolve().parent.parent/'scale-v2/checks.py'
spec=importlib.util.spec_from_file_location('rewrite_scale_checks',path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
make_cases=module.make_cases
