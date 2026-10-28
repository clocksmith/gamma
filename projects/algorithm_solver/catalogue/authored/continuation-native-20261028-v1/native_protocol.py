"""Host-only bridge to the existing judge's direct-class observation records."""
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('native_host_oracles', Path(__file__).with_name('oracles.py'))
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def packet(pid, cases, *, maximum_bytes):
    """Caller supplies its already approved packet cap; this grants no new cap."""
    if type(maximum_bytes) is not int or maximum_bytes <= 0:
        raise ValueError('existing positive exact packet bound required')
    if type(cases) is not list or not cases:
        raise ValueError('nonempty bounded case list required')
    calls = []
    for case in cases:
        if type(case) is not dict or 'args' not in case: raise ValueError('case arguments required')
        oracle.validate(pid, case['args'])
        calls.append({'args': case['args']})
    value = {'schema': 'gamma.native-class-transport.v1', 'native_problem_id': pid, 'calls': calls}
    raw = encoded(value)
    if len(raw) > maximum_bytes: raise ValueError('native packet exceeds existing caller bound')
    return raw


def check(pid, args, observed, expected, language):
    if language not in ('python', 'javascript'): raise ValueError('fixed language required')
    reason = oracle.check_observation(pid, args, observed, expected)
    if reason: return reason
    if (observed.get('native_route') != 'direct-class-v1' or observed.get('native_class') != oracle.CLASSES[pid] or
            type(observed.get('native_receiver_count')) is not int or observed['native_receiver_count'] != 1 or
            observed.get('result_type') != ('list' if language == 'python' else 'object') or
            not oracle.exact(observed.get('native_method_snapshots'), expected)):
        return 'native_interface'
    types = observed.get('native_method_return_types')
    if type(types) is not list or len(types) != len(args[0]) or types[0] != 'constructed':
        return 'native_interface'
    for name, kind in zip(args[0][1:], types[1:]):
        if name in ('totalScore', 'getHighestBidder') and kind != ('int' if language == 'python' else 'number'):
            return 'native_return_type'
        if name == 'matchDriverWithRider' and kind != ('list' if language == 'python' else 'object'):
            return 'native_return_type'
    return None
