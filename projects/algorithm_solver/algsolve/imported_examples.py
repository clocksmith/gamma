"""Source-bound repair of historical whitespace-collapsed LCD public inputs.

The original imported record is never mutated. This offline repair does not run
inside answer(), cannot change expected values, and uses no independent tests.
"""
from dataclasses import replace
import hashlib
import json
import re
from .public_examples import recover
from . import importers, values


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _historical_arguments(problem):
    """Reproduce the old transform on literal source, never decoded values."""
    result=[]
    for match in importers._EXAMPLE_RE.finditer(problem.statement):
        raw=re.sub(r"\\r(?=\r?\n|$)", "", match.group('input')).strip()
        args,kwargs=values.parse_call_arguments(' '.join(raw.split()))
        ordered=values.order_arguments(problem.params,args,kwargs)
        result.append([values.wrap_for_annotation(v,ann) for v,(_,ann) in zip(ordered,problem.params)])
    return result


def repair(problem):
    """Repair only a complete exact reproduction of the old input transform."""
    receipt = {'changed': False, 'reason': 'not_historical_lcd_public_inputs'}
    if (problem.source != 'lcd' or problem.uid != 'lcd:' + str(problem.source_id)
            or problem.import_notes.get('lcd_split') not in ('train', 'test')
            or problem.io_mode != 'functional' or not problem.public_tests):
        return problem, receipt
    parsed = recover(replace(problem, public_tests=[]))
    before, after = problem.public_tests, parsed.public_tests
    receipt = {'changed':False, 'source_statement_sha256':hashlib.sha256(problem.statement.encode()).hexdigest(),
               'source_interface_sha256':_digest([problem.entry,problem.params,problem.starter_code]),
               'old_public_sha256':_digest(before), 'parsed_public_sha256':_digest(after)}
    if not after or len(before) != len(after):
        return problem, dict(receipt,reason='incomplete_or_changed_example_count')
    if before == after:
        return problem, dict(receipt,reason='already_matches_source_literals')
    try:
        historical = _historical_arguments(problem)
    except (values.Unsupported, AssertionError):
        return problem, dict(receipt,reason='historical_transform_does_not_parse')
    if len(historical) != len(after):
        return problem, dict(receipt,reason='historical_example_count_changed')
    for old, new, old_args in zip(before, after, historical):
        # Require every old test field, including expected value and comparison,
        # to match. Only args may exhibit the known historical transformation.
        transformed = dict(new, args=old_args)
        if old != transformed:
            return problem, dict(receipt,reason='difference_not_explained_by_input_whitespace_collapse')
    repaired = replace(problem, public_tests=after)
    return repaired, dict(receipt,changed=True,reason='source_literal_input_whitespace_restored',
                          changed_examples=sum(a!=b for a,b in zip(before,after)),
                          expected_values_unchanged=True)
