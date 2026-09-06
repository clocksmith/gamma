#!/usr/bin/env python3
"""Reuse the sealed grammar driver for one five-arm argument-representation gate."""
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import dualstream_grammar_argtokens_v2 as codec

spec = importlib.util.spec_from_file_location(__name__ + "_driver", ROOT / "tools/dualstream_grammar_gate_v1.py")
driver = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = driver
spec.loader.exec_module(driver)
driver.SELF = "tools/dualstream_grammar_argtokens_gate_v2.py"
driver.CODEC = "tools/dualstream_grammar_argtokens_v2.py"
driver.codec = codec
original_validate = driver.validate_plan
original_phase = driver.run_phase


def validate_plan(plan, candidate):
    original_validate(plan, candidate)
    expected = [("P", "plain"), ("S", "split"), ("G", "grammar"), ("B", "parameter"), ("T", "parameter")]
    codec.require([(arm['id'], arm['mode']) for arm in plan['arms']] == expected, "five fixed arms required")
    codec.require(all(arm['config'] == dict(max_rule_length=4, grammar_budget=16, min_benefit=1, shortlist=4)
                      for arm in plan['arms']), "one diagnosed configuration only")
    codec.require(plan['stage'] == 'development', "this comparison is development only")


def run_phase(directory, phase, argv, plan, marker):
    # B independently reruns the immutable v1 parameter comparator.
    if phase.startswith('B-'):
        codec.require(argv[1] == str(ROOT / driver.CODEC), "unexpected comparator command")
        argv = [argv[0], str(ROOT / 'tools/dualstream_grammar_v1.py'), *argv[2:]]
    return original_phase(directory, phase, argv, plan, marker)


driver.validate_plan = validate_plan
driver.run_phase = run_phase


if __name__ == '__main__':
    raise SystemExit(driver.main())
