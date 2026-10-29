"""Host-only bridge to the existing judge's direct-class observation records for 729/731/732."""
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('gamma_r22a_native_host_oracles', Path(__file__).with_name('oracles.py'))
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)
BOOK_RETURN = {729: ('bool', 'boolean'), 731: ('bool', 'boolean'), 732: ('int', 'number')}


def exact(a, b):
    if type(a) is not type(b): return False
    if type(a) is list: return len(a) == len(b) and all(map(exact, a, b))
    return a == b


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def packet(pid, cases, *, maximum_bytes):
    """Caller supplies its already approved packet cap; this grants no new cap."""
    if type(maximum_bytes) is not int or maximum_bytes <= 0:
        raise ValueError('existing positive exact packet bound required')
    if type(pid) is not int or pid not in oracle.CLASSES or type(cases) is not list or not cases:
        raise ValueError('assigned native identity and nonempty bounded case list required')
    calls = []
    for case in cases:
        if type(case) is not dict or 'args' not in case: raise ValueError('case arguments required')
        oracle.validate_domain(pid, case['args'])
        calls.append({'args': case['args']})
    raw = encoded({'schema': 'gamma.native-class-transport.v1', 'native_problem_id': pid, 'calls': calls})
    if len(raw) > maximum_bytes: raise ValueError('native packet exceeds existing caller bound')
    return raw


def check(pid, args, observed, expected, language):
    if language not in ('python', 'javascript'): raise ValueError('fixed language required')
    oracle.validate_domain(pid, args)
    if type(observed) is not dict or 'error' in observed: return 'candidate_error'
    if not exact(observed.get('result'), expected): return 'wrong_answer'
    if (not exact(observed.get('args_before'), args) or not exact(observed.get('args_after'), args) or
            not exact(observed.get('alias_edges'), [])):
        return 'effects'
    if (observed.get('native_route') != 'direct-class-v1' or observed.get('native_class') != oracle.CLASSES[pid] or
            type(observed.get('native_receiver_count')) is not int or observed['native_receiver_count'] != 1 or
            observed.get('result_type') != ('list' if language == 'python' else 'object') or
            not exact(observed.get('native_method_snapshots'), expected)):
        return 'native_interface'
    kind = BOOK_RETURN[pid][0 if language == 'python' else 1]
    if not exact(observed.get('native_method_return_types'), ['constructed'] + [kind] * (len(args[0]) - 1)):
        return 'native_return_type'
    return None
