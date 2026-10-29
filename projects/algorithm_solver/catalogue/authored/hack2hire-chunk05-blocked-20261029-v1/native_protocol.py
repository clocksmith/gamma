"""Host-only bridge to the existing judge's direct-class observation records (hack2hire-chunk05-blocked, INFERRED interfaces)."""
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('gamma_h2h05x_native_host_oracles', Path(__file__).with_name('oracles.py'))
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)
# inferred return type per method -> (python type name, javascript typeof)
KIND = {'boolean': ('bool', 'boolean'), 'integer': ('int', 'number'), 'string': ('str', 'string'), 'string[]': ('list', 'object'),
        'integer[]': ('list', 'object'), 'void': ('NoneType', 'undefined')}
RETURNS = {
 "hack2hire:6a14a84c7b0582b352787d44": {
  "record": "void",
  "getLatestLux": "integer",
  "getAverageLux": "integer"
 },
 "hack2hire:67842117d0faf7ec64cc3add": {
  "playRound": "string",
  "getScore": "integer",
  "getWinner": "string"
 },
 "hack2hire:6784211bd0faf7ec64cc3ade": {
  "playRound": "string",
  "getScore": "integer",
  "getWinner": "string"
 },
 "hack2hire:694609632c048134ada83559": {
  "request": "string"
 }
}


def exact(a, b):
    if type(a) is not type(b): return False
    if type(a) is list: return len(a) == len(b) and all(map(exact, a, b))
    if type(a) is dict: return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    return a == b


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def packet(uid, cases, *, maximum_bytes):
    """Caller supplies its already approved packet cap; this grants no new cap."""
    if type(maximum_bytes) is not int or maximum_bytes <= 0:
        raise ValueError('existing positive exact packet bound required')
    if type(uid) is not str or uid not in oracle.CLASSES or type(cases) is not list or not cases:
        raise ValueError('assigned native identity and nonempty bounded case list required')
    calls = []
    for case in cases:
        if type(case) is not dict or 'args' not in case: raise ValueError('case arguments required')
        oracle.validate_domain(uid, case['args'])
        calls.append({'args': case['args']})
    raw = encoded({'schema': 'gamma.native-class-transport.v1', 'native_problem_id': uid, 'calls': calls})
    if len(raw) > maximum_bytes: raise ValueError('native packet exceeds existing caller bound')
    return raw


def check(uid, args, observed, expected, language):
    if language not in ('python', 'javascript'): raise ValueError('fixed language required')
    oracle.validate_domain(uid, args)
    if type(observed) is not dict or 'error' in observed: return 'candidate_error'
    if not exact(observed.get('result'), expected): return 'wrong_answer'
    if (not exact(observed.get('args_before'), args) or not exact(observed.get('args_after'), args) or
            not exact(observed.get('alias_edges'), [])):
        return 'effects'
    if (observed.get('native_route') != 'direct-class-v1' or observed.get('native_class') != oracle.CLASSES[uid][0] or
            type(observed.get('native_receiver_count')) is not int or observed['native_receiver_count'] != 1 or
            observed.get('result_type') != ('list' if language == 'python' else 'object') or
            not exact(observed.get('native_method_snapshots'), expected)):
        return 'native_interface'
    column = 0 if language == 'python' else 1
    kinds = ['constructed'] + [KIND[RETURNS[uid][op]][column] for op in args[0][1:]]
    if not exact(observed.get('native_method_return_types'), kinds):
        return 'native_return_type'
    return None
