"""Source-bound offline repairs of historical LCD public-example literals.

Recover four pinned argument/label formats or restore proven input-whitespace
collapse. Preserve original records and expected literal values. This does not
run inside answer() and never reads independent tests.
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



# These historical LCD records have no parsed public examples. Hashes bind the
# narrowly declared transformation to the original statement and full interface.
# Never use these options to guess semantics for arbitrary new user questions.
_PUBLIC_LITERAL_REPAIRS = {'lcd:1514': {'duplicate_output_label': False,
              'example_count': 3,
              'interface_sha256': '5335ce3c03e8ba4643d75562b94048d9be274116ff8c90a8747b8503fd622807',
              'parameter_aliases': {'end': 'end_node', 'start': 'start_node'},
              'statement_sha256': '5c935c75ca98c92806ad46770c9b491b6969d0d4125f5a83c52a63b44a314ada'},
 'lcd:2192': {'duplicate_output_label': False,
              'example_count': 2,
              'interface_sha256': '6c184a034e2d5d3964ad2ae4805f8d4439de184f2875006efc204701e96da1ed',
              'parameter_aliases': {'edgeList': 'edges'},
              'statement_sha256': 'f7c7f8949b8554c420278f17739706070cf66a06978c68723d64fd78b0ac119b'},
 'lcd:2711': {'duplicate_output_label': True,
              'example_count': 2,
              'interface_sha256': 'd3b6f5ffb03f31fc372ba292ef6b595b5d38296bb3789336fd59af9966924853',
              'parameter_aliases': {},
              'statement_sha256': '16314bebd09cfd2bd3243a78a974599689314a3ace87b4c3da0744497747a1fa'},
 'lcd:682': {'duplicate_output_label': False,
             'example_count': 3,
             'interface_sha256': 'd6941160c514cb0239e9702a816607e0f13a378ca514f21a225317806c9e5908',
             'parameter_aliases': {'ops': 'operations'},
             'statement_sha256': '3f0fe58f99edbfa32f60bad5fe25e93e23e7d66458ec73083ed023e2e2da5a9d'}}


def _repair_pinned_public_examples(problem):
    """Recover complete examples only for a matching frozen source/interface."""
    spec = _PUBLIC_LITERAL_REPAIRS.get(problem.uid)
    if spec is None:
        return None
    receipt = {'changed': False, 'repair': 'pinned-public-literals-v1',
               'source_statement_sha256': hashlib.sha256(problem.statement.encode()).hexdigest(),
               'source_interface_sha256': _digest([problem.entry, problem.params, problem.starter_code])}
    if (problem.source != 'lcd' or problem.uid != 'lcd:' + str(problem.source_id)
            or problem.import_notes.get('lcd_split') not in ('train', 'test')
            or problem.io_mode != 'functional' or problem.public_tests):
        return problem, dict(receipt, reason='ineligible_or_existing_public_examples')
    if (receipt['source_statement_sha256'] != spec['statement_sha256']
            or receipt['source_interface_sha256'] != spec['interface_sha256']):
        return problem, dict(receipt, reason='pinned_public_source_mismatch')
    try:
        method = problem.entry.get('method')
        params = values.signature(problem.starter_code, method)
        if [list(param) for param in params] != problem.params:
            return problem, dict(receipt, reason='pinned_public_interface_mismatch')
        tests, dropped = importers.statement_examples(
            problem.statement, params, values.return_annotation(problem.starter_code, method),
            parameter_aliases=spec['parameter_aliases'],
            duplicate_output_label=spec['duplicate_output_label'])
    except (values.Unsupported, AssertionError):
        return problem, dict(receipt, reason='pinned_public_parse_failure')
    if dropped or len(tests) != spec['example_count'] or not tests:
        return problem, dict(receipt, reason='incomplete_pinned_public_examples')
    return replace(problem, public_tests=tests), dict(
        receipt, changed=True, reason='pinned_public_literals_recovered',
        example_count=len(tests), parsed_public_sha256=_digest(tests),
        parameter_aliases=spec['parameter_aliases'],
        duplicate_output_label=spec['duplicate_output_label'],
        statement_and_interface_unchanged=True, expected_from_source_literal=True)


def repair(problem):
    """Try pinned format recovery, then proven historical whitespace repair.

    Return a new record and explicit receipt; never replace existing public
    examples except for the separately verified old whitespace transform.
    """
    pinned = _repair_pinned_public_examples(problem)
    if pinned is not None:
        return pinned
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
