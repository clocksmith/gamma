"""Finite, example-conditioned composition over a frozen development grammar.

This module has no task IDs, oracle imports, source lookup, or evaluation cases.
Every candidate is an inspectable typed graph. Search expands generic list
combinators into existing primitives; their names are not packet instructions.
The first training-consistent graph is frozen, even when later tests reject it.
"""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import time
from dataclasses import dataclass

from . import typed_vector_program as ir
from . import typed_word_codec as codec

SCHEMA = 'algsolve.direct-bits-search.v1'
MAX_CANDIDATES = 10000
MAX_EXAMPLES = 64
MAX_STAGES = 2
EXECUTION_BUDGET = 100000


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def ref(name): return {'ref': name}
def lit(value): return {'literal': value}
def expr(op, *args): return {'op': op, 'args': list(args)}
def bind(name, value, op='let'): return {'op': op, 'name': name, 'value': value}
def call(op, out, *args): return {'op': 'call', 'operator': op, 'out': out, 'args': list(args)}
def each(item, values, body): return {'op': 'for', 'item': item, 'in': values, 'body': body}
def branch(condition, yes, no=()): return {'op': 'if', 'condition': condition, 'then': yes, 'else': list(no)}


def scalar_terms():
    """Cost-ordered syntax, not a list indexed by problem identity."""
    atoms = ('x', 0, 1)
    result = list(atoms)
    result.extend(('neg', a) for a in atoms)
    for op in ('add', 'sub', 'mul'):
        for i, left in enumerate(atoms):
            for j, right in enumerate(atoms):
                if op in ('add', 'mul') and j < i:
                    continue
                result.append((op, left, right))
    # A generic guarded expression, expanded as a branch and mutable binding.
    result.append(('choose_negative', ('neg', 'x'), 'x'))
    return tuple(result)


def grammar():
    stages = [('map', t) for t in scalar_terms() if t != 'x']
    stages += [('filter', op) for op in ('positive', 'negative', 'nonzero')]
    stages += [('scan', 'add'), ('sort', False), ('sort', True), ('distinct',)]
    return {'schema': SCHEMA, 'max_stages': MAX_STAGES, 'stages': stages,
            'terminals': ('list', 'sum', 'product', 'length'),
            'candidate_order': 'stage-count, stage Cartesian product order, terminal order',
            'selection': 'first exact training match; no test-guided repair',
            'max_candidates': MAX_CANDIDATES, 'max_examples': MAX_EXAMPLES,
            'execution_budget': EXECUTION_BUDGET}


def scalar(term, item):
    if term == 'x': return ref(item)
    if type(term) is int: return lit(term)
    return expr(term[0], *(scalar(t, item) for t in term[1:]))


def compile_plan(stages, terminal):
    """Lower a small combinator sequence to fully explicit primitive data."""
    spec = grammar()
    if (type(stages) not in (list, tuple) or len(stages) > MAX_STAGES or
            terminal not in spec['terminals']):
        raise ValueError('Plan exceeds frozen grammar')
    allowed = {canonical(s) for s in spec['stages']}
    if any(canonical(s) not in allowed for s in stages):
        raise ValueError('Unknown stage')
    body = []
    values = ref('values')
    for index, stage in enumerate(stages):
        prefix = 's' + str(index)
        item, vector, output = prefix + 'item', prefix + 'vector', prefix + 'output'
        kind = stage[0]
        body.append(call('vector.new', vector))
        append = lambda value: call('vector.append', prefix + 'appended', ref(vector), value)
        if kind == 'map':
            term = stage[1]
            if type(term) in (list, tuple) and term[0] == 'choose_negative':
                loop = [bind(prefix + 'mapped', lit(0), 'var'),
                        branch(expr('lt', ref(item), lit(0)),
                               [bind(prefix + 'mapped', scalar(term[1], item), 'set')],
                               [bind(prefix + 'mapped', scalar(term[2], item), 'set')]),
                        append(ref(prefix + 'mapped'))]
            else:
                loop = [append(scalar(term, item))]
            body.append(each(item, values, loop))
        elif kind == 'filter':
            condition = {'positive': expr('lt', lit(0), ref(item)),
                         'negative': expr('lt', ref(item), lit(0)),
                         'nonzero': expr('not', expr('eq', ref(item), lit(0)))}[stage[1]]
            body.append(each(item, values, [branch(condition, [append(ref(item))])]))
        elif kind == 'scan':
            body.append(bind(prefix + 'sum', lit(0), 'var'))
            body.append(each(item, values, [
                bind(prefix + 'sum', expr('add', ref(prefix + 'sum'), ref(item)), 'set'),
                append(ref(prefix + 'sum'))]))
        elif kind == 'distinct':
            body.append(call('map.new', prefix + 'seen'))
            body.append(each(item, values, [
                call('map.has', prefix + 'present', ref(prefix + 'seen'), ref(item)),
                branch(expr('not', ref(prefix + 'present')), [
                    call('map.set', prefix + 'recorded', ref(prefix + 'seen'), ref(item), lit(1)),
                    append(ref(item))])]))
        elif kind == 'sort':
            body.append(call('heap.new', prefix + 'heap'))
            value = expr('neg', ref(item)) if stage[1] else ref(item)
            body.append(each(item, values, [call('heap.push', prefix + 'pushed', ref(prefix + 'heap'), value)]))
            value = expr('neg', ref(prefix + 'popped')) if stage[1] else ref(prefix + 'popped')
            body.append(each(prefix + 'unused', values, [
                call('heap.pop', prefix + 'popped', ref(prefix + 'heap')), append(value)]))
        body.append(call('vector.snapshot', output, ref(vector)))
        values = ref(output)
    output_type = ['list', 'int'] if terminal == 'list' else 'int'
    if terminal in ('sum', 'product'):
        body.append(bind('answer', lit(0 if terminal == 'sum' else 1), 'var'))
        body.append(each('term', values, [bind('answer', expr('add' if terminal == 'sum' else 'mul',
                                                           ref('answer'), ref('term')), 'set')]))
        answer = ref('answer')
    elif terminal == 'length':
        answer = expr('len', values)
    else:
        answer = values
    program = {'schema': ir.SCHEMA, 'parameters': ['values'], 'inputs': {'values': ['list', 'int']},
               'body': body, 'return': answer, 'output_type': output_type}
    ir.validate(program)
    return program


def candidates():
    spec = grammar()
    for count in range(MAX_STAGES + 1):
        for stages in itertools.product(spec['stages'], repeat=count):
            for terminal in spec['terminals']:
                yield {'stages': stages, 'terminal': terminal}, compile_plan(stages, terminal)


class ExecutionFailure(ir.Invalid):
    def __init__(self, cause, attempted_units, budget):
        super().__init__(str(cause))
        self.cause = type(cause).__name__
        self.attempted_operation_units = attempted_units
        self.operation_units = min(attempted_units, budget)


def _run_validated(program, positional_inputs, budget=EXECUTION_BUDGET):
    """Run a previously validated graph, with boundary checks on every call.

    The only avoided work is repeating graph validation. No candidate Python or
    JavaScript is executed; private _run is the unchanged bounded IR engine.
    Callers must validate their local graph before using this internal helper.
    """
    if type(budget) is not int or not 0 < budget <= 2000000:
        raise ValueError('Invalid operation budget')
    if type(positional_inputs) not in (tuple, list) or len(positional_inputs) != len(program['parameters']):
        raise ValueError('Positional input arity mismatch')
    for name, value in zip(program['parameters'], positional_inputs):
        ir.check_value(value, ir.dtype(program['inputs'][name]))
    meter = ir.Budget(budget)
    try:
        answer = ir._run(program, copy.deepcopy(list(positional_inputs)), {}, meter)
        ir.check_value(answer, ir.dtype(program['output_type']))
    except ir.Invalid as exc:
        raise ExecutionFailure(exc, budget - meter.remaining, budget) from exc
    return answer, budget - meter.remaining


def run_graph(program, positional_inputs, budget=EXECUTION_BUDGET):
    """Public checked graph runner; packets use evaluate_packet instead."""
    ir.validate(program)
    return _run_validated(program, positional_inputs, budget)


@dataclass
class SearchResult:
    selections: list
    trace: list
    candidates_tested: int
    training_executions: int
    training_operation_units: int
    training_attempted_operation_units: int
    failed_training_executions: int
    elapsed_seconds: float


def synthesize(requests, *, candidate_limit=MAX_CANDIDATES):
    """Each request is [(positional_inputs, expected), ...], with no metadata.

    Multiple requests share a deterministic search pass. Expected answers stay
    in this host comparator, never in the candidate's graph or argument values.
    Errors eliminate a candidate, not its cases. Empty evidence fails closed.
    """
    if (type(requests) not in (tuple, list) or not requests or len(requests) > 64 or
            type(candidate_limit) is not int or not 0 < candidate_limit <= MAX_CANDIDATES):
        raise ValueError('Invalid search bounds')
    for cases in requests:
        if not cases or len(cases) > MAX_EXAMPLES:
            raise ValueError('Require nonempty bounded training evidence')
    inputs = [case[0] for case in requests[0]]
    if any(canonical([case[0] for case in cases]) != canonical(inputs) for cases in requests):
        raise ValueError('Batch requests must share ordered training inputs')
    # Validate primitive boundary values before enumerating any graphs.
    for args in inputs:
        if type(args) not in (tuple, list) or len(args) != 1:
            raise ValueError('Expected one positional integer list')
        ir.check_value(args[0], ir.INTS)
    targets = {}
    for index, cases in enumerate(requests):
        expected = [case[1] for case in cases]
        for value in expected:
            ir.check_value(value, ir.INTS if type(value) is list else 'int')
        targets.setdefault(canonical(expected), []).append(index)
    selected = [None] * len(requests)
    trace = []
    executions = units = attempted = failed_executions = 0
    started = time.perf_counter()
    for ordinal, (plan, program) in enumerate(itertools.islice(candidates(), candidate_limit)):
        observed = []
        failure = None
        for args in inputs:
            executions += 1
            try:
                result, used = _run_validated(program, args)
                units += used
                attempted += used
                observed.append(result)
            except ExecutionFailure as exc:
                units += exc.operation_units
                attempted += exc.attempted_operation_units
                failed_executions += 1
                failure = str(exc)
                break
            except ir.Invalid as exc:
                failed_executions += 1
                failure = str(exc)
                break
        matches = [] if failure else targets.get(canonical(observed), [])
        new = [i for i in matches if selected[i] is None]
        row = {'ordinal': ordinal, 'plan': plan, 'graph_sha256': digest(program),
               'training_behavior_sha256': digest(observed), 'failure': failure,
               'new_matches': new}
        trace.append(row)
        if new:
            packet, cost = codec.encode(program, 6, 'vector-v1')
            selection = {'ordinal': ordinal, 'plan': copy.deepcopy(plan),
                         'packet_hex': packet.hex(), 'packet_sha256': hashlib.sha256(packet).hexdigest(),
                         'graph_sha256': digest(codec.decode(packet)), 'packet_cost': cost}
            for index in new:
                selected[index] = copy.deepcopy(selection)
        if all(item is not None for item in selected):
            break
    return SearchResult(selected, trace, len(trace), executions, units, attempted,
                        failed_executions, time.perf_counter() - started)


def evaluate_packet(packet, cases, *, budget=EXECUTION_BUDGET):
    """Independent host comparison after selection; never repairs or searches.

    Cases are (positional_inputs, expected). Packet validation/decoding is done
    once; every execution has fresh owned state, copied inputs and a new budget.
    """
    if not cases:
        raise ValueError('Empty evaluation is not evidence')
    program = codec.decode(packet)
    if program['schema'] != ir.SCHEMA:
        raise ValueError('Direct v1 evaluates the owned-vector profile only')
    failures = []
    passed = total_units = attempted_units = max_units = 0
    observations = []
    for index, (inputs, expected) in enumerate(cases):
        before = copy.deepcopy(inputs)
        try:
            observed, used = _run_validated(program, inputs, budget)
            unchanged = inputs == before
            correct = canonical(observed) == canonical(expected) and unchanged
            total_units += used
            attempted_units += used
            max_units = max(max_units, used)
            observations.append({'observed': observed, 'units': used, 'input_preserved': unchanged})
            if correct:
                passed += 1
            else:
                failures.append({'case': index, 'observed': observed, 'expected': expected,
                                 'input_preserved': unchanged, 'reason': 'wrong_result'})
        except ExecutionFailure as exc:
            total_units += exc.operation_units
            attempted_units += exc.attempted_operation_units
            max_units = max(max_units, exc.operation_units)
            failures.append({'case': index, 'reason': exc.cause, 'detail': str(exc),
                             'operation_units': exc.operation_units,
                             'attempted_operation_units': exc.attempted_operation_units})
            observations.append({'error': exc.cause, 'detail': str(exc),
                                 'operation_units': exc.operation_units,
                                 'attempted_operation_units': exc.attempted_operation_units})
        except (ir.Invalid, ValueError) as exc:
            failures.append({'case': index, 'reason': type(exc).__name__, 'detail': str(exc)})
            observations.append({'error': type(exc).__name__, 'detail': str(exc)})
    return {'passed': passed == len(cases), 'cases': len(cases), 'passed_cases': passed,
            'failures': failures, 'total_operation_units': total_units,
            'total_attempted_operation_units': attempted_units,
            'max_case_operation_units': max_units, 'execution_budget': budget,
            'observations_sha256': digest(observations),
            'case_set_sha256': digest(cases), 'packet_sha256': hashlib.sha256(packet).hexdigest()}
