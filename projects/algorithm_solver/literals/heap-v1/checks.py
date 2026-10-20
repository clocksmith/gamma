"""Reuse unchanged independent development inputs for1046."""
import importlib.util
from pathlib import Path
p=Path(__file__).resolve().parent.parent/"scale-v2/checks.py"
spec=importlib.util.spec_from_file_location("heap_cases",p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
make_cases=m.make_cases
