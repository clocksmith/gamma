"""Authored fault-injection diagnostic, not a frozen-model comparison.

No corpus, checkpoint, embedding, protected cases, source evaluator or native
judge is used. Synthetic scores favor the known original token as runner-up;
these intentionally favorable rankings do not estimate model performance.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import platform
import time

from . import typed_codec, typed_program
from .typed_correction import correct, validate_codes
from .typed_prediction_codec import INPUTS, OPS, PredictionCodec
from .typed_recipes import assign, branch, lit, program, pure, ref


SCHEMA = 'algsolve.typed-synthetic-fault-diagnostic.v1'
# A new diagnostic policy, not a revision or qualification of the frozen one.
CORRECTION = {
    'fields': ['op', 'first', 'next', 'binding', 'types'],
    'alternatives_per_field': 2,
    'max_edit_options': 64,
    'max_edits': 2,
    'max_candidates': 128,
    'wall_seconds': 0.2,
}
EXECUTION_BUDGET = 1000
PARAMETERS = {'x': 'int', 'y': 'int', 'flag': 'bool'}


def fixtures():
    """Return two small authored programs and explicit, non-sealed expectations."""
    addition = program(PARAMETERS, [], pure('add', ref('x'), ref('y')), 'int')
    scoped = program(PARAMETERS, [branch(ref('flag'), [assign('local', lit(7))])],
                     ref('x'), 'int')
    inputs = [dict(x=2, y=2, flag=True), dict(x=5, y=1, flag=False),
              dict(x=-3, y=7, flag=True), dict(x=0, y=0, flag=False)]
    return {
        'addition': {'program': addition, 'inputs': inputs, 'expected': [4, 6, 4, 0]},
        'scope': {'program': scoped, 'inputs': inputs, 'expected': [2, 5, -3, 0]},
    }


def capture(encoding, graph):
    """Create explicit synthetic argmax scores without a predictor or model."""
    codes = encoding.encode(graph)
    for field, values in codes.items():
        codes[field] = ([[max(0, item) for item in row] for row in values]
                        if field == 'bits' else [max(0, item) for item in values])
    return codes


def scores_from_recipe(codes, injected_edits, slots, type_count):
    """Losslessly reconstruct the dense scores from the retained sparse recipe."""
    sizes = {'op': len(OPS), 'first': slots + 1, 'next': slots + 1,
             'binding': INPUTS + slots, 'types': type_count}
    scores = {}
    for field, size in sizes.items():
        scores[field] = [[-100.] * size for _ in codes[field]]
        for index, value in enumerate(codes[field]):
            scores[field][index][value] = 10.
    for edit in injected_edits:
        scores[edit['field']][edit['slot']][edit['from']] = 9.
    return scores


def cases(encoding, authored):
    """Axes are injected labels, not inferred frequencies of neural failures."""
    originals = {key: capture(encoding, fixture['program']) for key, fixture in authored.items()}
    addition = originals['addition']
    sequence = addition['op'].index(OPS.index('sequence'))
    operator = addition['op'].index(OPS.index('pure:add'))
    refs = [i for i, value in enumerate(addition['op']) if value == OPS.index('ref')]
    scope = originals['scope']
    local = scope['op'].index(OPS.index('let'))
    return_ref = max(i for i, value in enumerate(scope['op']) if value == OPS.index('ref'))
    missing_binding = INPUTS + encoding.slots - 1
    specs = [
        ('control-addition', 'control', 'addition', []),
        ('control-scope', 'control', 'scope', []),
        ('structure-root-cycle', 'structural', 'addition', [('first', 0, 1)]),
        ('structure-sibling-cycle', 'structural', 'addition', [('next', refs[0], refs[0] + 1)]),
        ('structure-missing-root-children', 'structural', 'addition', [('first', 0, 0)]),
        ('structure-interior-empty', 'structural', 'addition', [('op', sequence, OPS.index('EMPTY'))]),
        ('binding-unknown', 'binding', 'addition', [('binding', refs[0], missing_binding)]),
        ('binding-escaped-branch-local', 'binding', 'scope', [('binding', return_ref, INPUTS + local)]),
        ('binding-wrong-type', 'binding', 'addition', [('binding', refs[1], 2)]),
        ('binding-valid-but-wrong', 'binding', 'addition', [('binding', refs[0], 1)]),
        ('operation-wrong-arity', 'operation', 'addition', [('op', operator, OPS.index('pure:neg'))]),
        ('operation-wrong-result-type', 'operation', 'addition', [('op', operator, OPS.index('pure:eq'))]),
        ('operation-valid-but-wrong', 'operation', 'addition', [('op', operator, OPS.index('pure:mul'))]),
        ('combined-structure-binding', 'combined', 'addition',
         [('first', 0, 1), ('binding', refs[0], missing_binding)]),
    ]
    result = []
    for name, axis, fixture, mutations in specs:
        raw = copy.deepcopy(originals[fixture])
        edits = []
        for field, slot, value in mutations:
            old = raw[field][slot]
            if old == value:
                raise ValueError('Fault injection must change a coordinate')
            edits.append({'field': field, 'slot': slot, 'from': old, 'to': value})
            raw[field][slot] = value
        result.append({'case': name, 'axis': axis, 'fixture': fixture,
                       'injected_edits': edits, 'raw_codes': raw})
    return result


def check_graph(graph, fixture):
    """Check bounded, repository-owned typed data; never execute source code."""
    if graph is None:
        return {'status': 'not_executed_invalid_graph', 'passed': None, 'checks': []}
    checks = []
    for inputs, expected in zip(fixture['inputs'], fixture['expected']):
        supplied = copy.deepcopy(inputs)
        try:
            actual = typed_program.execute(graph, supplied, budget=EXECUTION_BUDGET)
            preserved = supplied == inputs
            checks.append({'input': inputs, 'expected': expected, 'actual': actual,
                           'input_preserved': preserved,
                           'passed': type(actual) is type(expected) and actual == expected and preserved})
        except typed_program.Invalid as error:
            checks.append({'input': inputs, 'expected': expected,
                           'error': str(error), 'passed': False})
    return {'status': 'authored_fixture_checks', 'passed': bool(checks) and all(c['passed'] for c in checks),
            'checks': checks}


def outcome(row):
    raw = row['raw']['fixture_checks']['passed'] is True
    fixed = row['constrained']['fixture_checks']['passed'] is True
    if raw and not fixed:
        return 'harmful_on_authored_checks'
    if fixed and not raw:
        return 'useful_on_authored_checks'
    if row['raw']['graph_sha256'] == row['constrained']['graph_sha256']:
        return 'unchanged'
    return 'validity_only_or_other_neutral'


def summarize(rows):
    result = {}
    for axis in ['all', 'control', 'structural', 'binding', 'operation', 'combined']:
        selected = rows if axis == 'all' else [r for r in rows if r['axis'] == axis]
        result[axis] = {'cases': len(selected)}
        for route in ['raw', 'constrained']:
            result[axis][route] = {
                'valid': sum(r[route]['graph'] is not None for r in selected),
                'passes_authored_checks': sum(r[route]['fixture_checks']['passed'] is True for r in selected),
                'valid_but_fails_authored_checks': sum(r[route]['fixture_checks']['passed'] is False for r in selected),
                'invalid_not_executed': sum(r[route]['graph'] is None for r in selected),
            }
        for category in ['useful_on_authored_checks', 'harmful_on_authored_checks',
                         'unchanged', 'validity_only_or_other_neutral']:
            result[axis][category] = sum(r['outcome'] == category for r in selected)
    return result


def run_diagnostic():
    authored = fixtures()
    encoding = PredictionCodec.fit([
        {'learning_split': 'development_fit', 'target': {'program': item['program']}}
        for item in authored.values()
    ])
    rows = []
    # Phase one fixes every graph and correction before any expected-value check.
    for case in cases(encoding, authored):
        raw = case['raw_codes']
        raw_hash = typed_codec.digest(raw)
        params = authored[case['fixture']]['program']['parameters']
        scores = scores_from_recipe(raw, case['injected_edits'], encoding.slots, len(encoding.types))
        started = time.perf_counter()
        graph, failure = validate_codes(encoding, raw, params)
        raw_seconds = time.perf_counter() - started
        repaired = correct(encoding, raw, scores, params, CORRECTION)
        if typed_codec.digest(raw) != raw_hash:
            raise ValueError('Correction mutated the retained raw capture')
        fixed = repaired.pop('graph')
        row = {**case, 'raw_sha256': raw_hash, 'scores_sha256': typed_codec.digest(scores),
               'raw': {'graph': graph, 'graph_sha256': typed_codec.digest(graph) if graph is not None else None,
                       'validation_failure': failure, 'validation_seconds': raw_seconds},
               'constrained': {'graph': fixed,
                               'graph_sha256': typed_codec.digest(fixed) if fixed is not None else None,
                               'correction': repaired}}
        row['fixed_decisions_sha256'] = typed_codec.digest(row)
        rows.append(row)
    # These expectations are authored diagnostics, not independent sealed tests.
    for row in rows:
        fixture = authored[row['fixture']]
        for route in ['raw', 'constrained']:
            row[route]['fixture_checks'] = check_graph(row[route]['graph'], fixture)
        row['outcome'] = outcome(row)
    source_names = ['typed_synthetic_diagnostic.py', 'typed_prediction_codec.py',
                    'typed_correction.py', 'typed_codec.py', 'typed_program.py', 'typed_recipes.py']
    sources = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
               for name in source_names}
    return {
        'schema': SCHEMA,
        'evidence_class': 'authored_synthetic_fault_injection_only',
        'protected_data_read': False, 'model_used': False, 'trained': False,
        'native_judge_used': False, 'frozen_model_comparison_recreated': False,
        'development_qualified': False, 'protected_scoring_authorized': False,
        'autonomous_loop_ready': False,
        'runtime': {'python': platform.python_version(), 'platform': platform.platform()},
        'source_sha256': sources, 'prediction_descriptor': encoding.descriptor(),
        'correction_policy': CORRECTION, 'execution_budget': EXECUTION_BUDGET,
        'synthetic_scores': {
            'recipe': 'Every field/slot has score -100 except raw argmax 10. Each injected original value has score 9.',
            'literal_scores': 'Literal bit values are retained; no bit correction or bit logits.',
            'reconstruction': 'Use scores_from_recipe(raw_codes, injected_edits, slots, type_count).',
            'warning': 'Original-token runner-up scores are deliberately favorable synthetic data, not model predictions.',
        },
        'fixtures': authored, 'summary': summarize(rows), 'cases': rows,
        'limitations': [
            'Fourteen designed perturbations of two authored fixtures, not 14 independent problems.',
            'Injected axis labels do not measure the distribution of actual predictor errors.',
            'No checkpoint, embedding or frozen development corpus was reconstructed.',
            'Authored expectation checks are neither unseen scoring nor native sandbox qualification.',
            'Valid-but-wrong graphs must remain unchanged; schema repair is not semantic algorithm repair.',
            'Correction/validation time excludes model, embedding, source assembly and native public checking.',
            'Wall-clock limits may stop work earlier on another machine; retain that outcome without retuning.',
        ],
    }


def report_text(result):
    lines = ['# Synthetic typed-composer fault diagnostic', '',
             'Authored fixtures only. This is not the frozen model comparison, a solver qualification,',
             'a native-judge result, or protected/unseen scoring.', '',
             '| Injected axis | Cases | Raw valid | Corrected valid | Raw fixture pass | Corrected fixture pass | Useful | Harmful |',
             '|---|---:|---:|---:|---:|---:|---:|---:|']
    for axis, counts in result['summary'].items():
        raw, fixed = counts['raw'], counts['constrained']
        lines.append(f"| {axis} | {counts['cases']} | {raw['valid']} | {fixed['valid']} | "
                     f"{raw['passes_authored_checks']} | {fixed['passes_authored_checks']} | "
                     f"{counts['useful_on_authored_checks']} | {counts['harmful_on_authored_checks']} |")
    lines.extend(['', '## Per-case results', ''])
    for row in result['cases']:
        repair = row['constrained']['correction']
        lines.append(f"- {row['case']}: {repair['reason']}; {len(repair['edits'])} edits; "
                     f"{len(repair['attempts'])} candidates; {row['outcome']}.")
    lines.extend(['', '## Limits', '', *['- ' + item for item in result['limitations']], ''])
    return '\n'.join(lines)


def write_result(output, result):
    """Keep each run immutable; never silently replace an earlier receipt."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    # Captures retain every slot/bit; compact JSON avoids megabytes of padding.
    (output / 'diagnostic.json').write_text(json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n')
    (output / 'report.md').write_text(report_text(result))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New directory for synthetic-only evidence')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output directory already exists; preserve prior evidence')
    result = run_diagnostic()
    write_result(args.output, result)
    print(json.dumps({'evidence_class': result['evidence_class'], 'summary': result['summary'],
                      'output': str(args.output)}, indent=2))


if __name__ == '__main__':
    main()
