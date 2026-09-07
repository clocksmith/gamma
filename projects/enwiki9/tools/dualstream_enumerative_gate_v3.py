#!/usr/bin/env python3
"""Preserve retained baseline frontends in the bounded enumerative comparison.

The previous runner and codecs remain immutable. This explicit adapter changes
plain-baseline format dispatch only; enum bytes and the chosen graph are fixed.
"""
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNNER = 'tools/dualstream_enumerative_gate_v2.py'
spec = importlib.util.spec_from_file_location(__name__ + '_runner', ROOT / RUNNER)
gate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate
spec.loader.exec_module(gate)
gate.driver.SELF = 'tools/dualstream_enumerative_gate_v3.py'
gate.DECODER = 'tools/dualstream_grammar_decode_dispatch_v1.py'
gate.PACKAGE = gate.PACKAGE + [gate.DECODER]
gate.ARMS[0] = dict(id='P', selection='plain', backend='deflate', storage='new')
original_validate = gate.validate_plan


def validate_plan(plan, candidate):
    original_validate(plan, candidate)
    for arm in gate.ARMS:
        if arm['backend'] == 'deflate':
            path = ROOT / plan['selected_archives'][arm['selection']]['path']
            with path.open('rb') as source:
                magic = source.read(8)
            gate.require(magic == (b'D2GRAM01' if arm['storage'] == 'old' else b'D2GRAM02'),
                         'diagonal storage differs from selected frontend')


gate.driver.validate_plan = validate_plan


if __name__ == '__main__':
    raise SystemExit(gate.main())
