"""Boundary-lane record checker for 126 and 140; the frozen Q and repair checkers stay unchanged.

Rows the existing checkers can judge (their bounded oracles and certificates)
are delegated to them unchanged. Rows beyond those budgets are judged against a
value recomputed from the args by this lane's independent reference
(boundary_cases.independent_expected). No supplied expected value is accepted.
The route, read-only effect, type and unordered-distinct checks repeat the
frozen Q checker's non-native rules exactly.
"""
import importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent
AUTHORED = HERE.parent/'authored'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


cases = load(HERE/'boundary_cases.py', 'q_boundary_check_cases')
INNER = {126: load(AUTHORED/'continuation-q126-output-sensitive-20261028-v1'/'host_check.py', 'q_boundary_inner_126'),
         140: load(AUTHORED/'continuation-q140-output-sensitive-20261028-v1'/'host_check.py', 'q_boundary_inner_140')}
METHODS = {126: 'findLadders', 140: 'wordBreak'}


def within_existing(pid, args):
    """True when the unchanged repair/Q checker can compute this row itself."""
    try:
        INNER[pid].expected(pid, args)
    except ValueError:
        return False
    return True


def expected(pid, args):
    if type(pid) is not int or pid not in INNER:
        raise ValueError('boundary bridge covers 126 and 140 only')
    if within_existing(pid, args):
        return INNER[pid].expected(pid, args)
    return cases.independent_expected(pid, args)


def check_observation(pid, args, record, language):
    try:
        if type(pid) is not int or pid not in INNER:
            return False, 'wrong_boundary_identity'
        if within_existing(pid, args):
            return INNER[pid].check_observation(pid, args, record, language)
        wanted = cases.independent_expected(pid, args)
        if language not in ('python', 'javascript') or type(record) is not dict or 'error' in record:
            return False, 'observation_shape'
        entry = 'python-solution-method' if language == 'python' else 'javascript-official-function'
        if (record.get('native_route') != 'official-wrapper-q-v1' or record.get('entry_kind') != entry or type(record.get('problem_id')) is not int
                or record['problem_id'] != pid or record.get('method') != METHODS[pid]):
            return False, 'official_route'
        exact = INNER[pid].original.exact
        if not exact(record.get('args_before'), args):
            return False, 'argument_before'
        if (not exact(record.get('args_after'), args) or not exact(record.get('alias_edges'), [])
                or record.get('node_identity') is not None or record.get('node_integrity') is not None):
            return False, 'ordinary_effects'
        result = record.get('result')
        if record.get('result_type') != ('list' if language == 'python' else 'object') or type(result) is not list:
            return False, 'result_type'
        if pid == 126:
            if any(type(path) is not list or any(type(word) is not str for word in path) for path in result):
                return False, 'result_type'
            actual = [tuple(path) for path in result]; desired = [tuple(path) for path in wanted]
        else:
            if any(type(value) is not str for value in result):
                return False, 'result_type'
            actual = result; desired = wanted
        return (True, None) if len(set(actual)) == len(actual) and set(actual) == set(desired) else (False, 'unordered_distinct_result')
    except (ValueError, TypeError, KeyError, IndexError, OverflowError, RecursionError):
        return False, 'invalid_or_unsupported_observation'
