#!/usr/bin/env python3
"""Immutable v1 diagnostic with exact authentication of empty runtime files."""
import hashlib
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
V1 = 'tools/opcode_event_opportunity_decode250k_q0_v1.py'
V1_SHA256 = '8fff58fd71d94fa1be77a385ba93da226aa3f0ae4477516dcfc949dbc072f5c2'


def load_original(path):
    source = path.read_bytes()
    if path.resolve() != path or hashlib.sha256(source).hexdigest() != V1_SHA256:
        raise ValueError('immutable v1 diagnostic source differs')
    module = types.ModuleType(__name__ + '_authenticated_v1')
    module.__file__ = str(path)
    exec(compile(source, str(path), 'exec'), vars(module))
    return module


original = load_original(ROOT/V1)
CID = 'opcode_event_opportunity_decode250k_q0_v2'
SELF = 'tools/' + CID + '.py'
INPUTS = 'operations/provenance/opcode_event_opportunity_decode250k_v2_inputs.json'
SOURCES = original.SOURCES | {SELF, 'tests/test_' + CID + '.py'}
CAPS, PHASES, EXPECTED, SCHEMA = original.CAPS, original.PHASES, original.EXPECTED, original.SCHEMA
phase, binding, require = original.phase, original.binding, original.require
EventSink, RECORD, SENTINEL = original.EventSink, original.RECORD, original.SENTINEL
ceil_log2_ratio, decode_phase = original.ceil_log2_ratio, original.decode_phase


def check_runtime_file(row):
    if not isinstance(row, dict) or row.get('bytes') != 0:
        return binding.check_file(row, absolute=True)
    require(set(row) == {'path', 'bytes', 'sha256'} and type(row['bytes']) is int
            and isinstance(row['path'], str) and binding.hash_text(row['sha256']), 'invalid empty runtime reference')
    path = Path(row['path'])
    require(path.is_absolute() and '..' not in path.parts and str(path) == row['path']
            and path.is_file(), 'missing or unsafe empty runtime file')
    require(path.stat().st_size == 0 and phase.sha(path) == row['sha256'], 'changed empty runtime file')
    return path


def verify_inputs(plan):
    for row in [*(plan[name] for name in original.PRIMARY), *plan['source_files'], *plan['evidence']]:
        binding.check_file(row)
    for row in plan['runtime_files']:
        check_runtime_file(row)


# Only identity/closure and runtime authentication differ. The shared globals
# mapping preserves the unchanged controller, phase commands and science.
_scope = dict(vars(original), CID=CID, SELF=SELF, INPUTS=INPUTS, SOURCES=SOURCES, verify_inputs=verify_inputs)
for _name in ('validate_plan', 'authenticate', 'run_comparison', 'main'):
    _source = getattr(original, _name)
    _scope[_name] = types.FunctionType(_source.__code__, _scope, _name, _source.__defaults__)
validate_plan, authenticate, run_comparison, main = [_scope[n] for n in ('validate_plan', 'authenticate', 'run_comparison', 'main')]


if __name__ == '__main__':
    raise SystemExit(main())
