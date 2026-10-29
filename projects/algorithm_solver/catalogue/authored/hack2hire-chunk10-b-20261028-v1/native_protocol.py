"""Host-only bridge to the existing judge's direct-class observation records (hack2hire-chunk10-b, INFERRED interfaces)."""
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('gamma_h2h10b_native_host_oracles', Path(__file__).with_name('oracles.py'))
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)
# inferred return type per method -> (python type name, javascript typeof)
KIND = {'boolean': ('bool', 'boolean'), 'integer': ('int', 'number'), 'string': ('str', 'string'), 'string[]': ('list', 'object'),
        'integer[]': ('list', 'object'), 'void': ('NoneType', 'undefined')}
RETURNS = {
 "hack2hire:695d85f19c1c1f40daea73a0": {
  "setPolicy": "void",
  "consume": "boolean",
  "getTokens": "integer"
 },
 "hack2hire:68a4bbecc11d63d6052ea307": {
  "addWorker": "boolean",
  "registerWorker": "string",
  "get": "integer"
 },
 "hack2hire:68a4bbf8c11d63d6052ea308": {
  "addWorker": "boolean",
  "registerWorker": "string",
  "get": "integer",
  "topNWorkers": "string"
 },
 "hack2hire:68a4bbfac11d63d6052ea309": {
  "addWorker": "boolean",
  "registerWorker": "string",
  "get": "integer",
  "topNWorkers": "string",
  "promote": "string",
  "calcSalary": "integer"
 },
 "hack2hire:68a4bbfbc11d63d6052ea30a": {
  "addWorker": "boolean",
  "registerWorker": "string",
  "get": "integer",
  "topNWorkers": "string",
  "promote": "string",
  "calcSalary": "integer",
  "setDoublePaid": "void"
 },
 "hack2hire:69efc8ea96981f58ae1f6d74": {
  "addTask": "string",
  "updateTask": "boolean",
  "getTask": "string"
 },
 "hack2hire:69efc92d96981f58ae1f6d75": {
  "addTask": "string",
  "updateTask": "boolean",
  "getTask": "string",
  "searchTasks": "string[]",
  "listTasksSorted": "string[]"
 },
 "hack2hire:69efc94196981f58ae1f6d76": {
  "addTask": "string",
  "updateTask": "boolean",
  "getTask": "string",
  "searchTasks": "string[]",
  "listTasksSorted": "string[]",
  "addUser": "boolean",
  "assignTask": "boolean",
  "getUserTasks": "string[]"
 },
 "hack2hire:69efc96396981f58ae1f6d77": {
  "addTask": "string",
  "updateTask": "boolean",
  "getTask": "string",
  "searchTasks": "string[]",
  "listTasksSorted": "string[]",
  "addUser": "boolean",
  "assignTask": "boolean",
  "getUserTasks": "string[]",
  "completeTask": "boolean",
  "getOverdueAssignments": "string[]"
 },
 "hack2hire:69026c73d18315042523a913": {
  "next": "string",
  "prev": "string",
  "goTo": "string"
 },
 "hack2hire:685637ce4d16ce2ead6e1769": {
  "encode": "string[]",
  "decode": "integer[]"
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
