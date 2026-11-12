"""Controlled comparison: bit-flip literal repair vs the value-coherent policy
(literal-value-v1), on the ten sealed literal-margin fit captures.

Arms (identical budgets: 2 s decision ceiling, literal stage .25 s and 4
executions shared with recipe repair, guard filter on both repaired arms):
  control       constrained route only
  bitflip       guarded semantic route with the existing bit-flip literal search
  value         guarded semantic route with literal-value-v1
Solver records are sealed before independent tests are loaded.

  PYTHONPATH=<tree>/projects/algorithm_solver python run_value.py --lane <checkout lane> --out <new dir>
"""
import argparse, hashlib, json, time
from pathlib import Path

from algsolve.records import load_hidden_tests
from algsolve.synth import typed_codec, development_tests, mine
from algsolve.synth.train_typed import problem_for
from algsolve.synth.typed_prediction_codec import PredictionCodec
from algsolve.synth.typed_comparison import run_route, score_fixed
from algsolve.synth.typed_semantic_repair import run_semantic_route
from algsolve.synth.typed_guard_filter import unreachable_numeric_guard
from algsolve.synth.typed_literal_value_repair import literal_value_search, POLICY

ARMS = ('control', 'bitflip', 'value')


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, indent=1, sort_keys=True) + '\n')


def repair_stats(route):
    semantic = route.get('semantic_repair') or {}
    literal = semantic.get('literal_repair') or {}
    attempts = literal.get('attempts', [])
    final = attempts[-1] if attempts and route.get('reason') == 'literal_public_passed' else None
    def bits_of(attempt):
        return attempt.get('bit_changes', len(attempt.get('edits', [])))
    def fields_of(attempt):
        return attempt.get('field_edits', len({e['slot'] for e in attempt.get('edits', [])}))
    return dict(executions=semantic.get('executions', 0), literal_executions=literal.get('executions', 0),
                literal_attempts=len(attempts), literal_reason=literal.get('reason'),
                accepted_field_edits=fields_of(final) if final else None,
                accepted_bit_changes=bits_of(final) if final else None,
                searched_bit_changes=sum(bits_of(a) for a in attempts),
                searched_field_edits=sum(fields_of(a) for a in attempts),
                repair_seconds=route['timing'].get('semantic_seconds', 0.))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lane', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    root, out = args.lane, args.out
    out.mkdir(parents=True, exist_ok=False)
    old = root/'runs/typed-literal-margin-fit-128-v1'
    load = lambda p: json.loads(Path(p).read_text())
    frozen, seal = load(old/'candidate.json'), load(old/'capture-seal.json')
    for name, digest in seal['captures_sha256'].items():
        assert hashlib.sha256((old/name).read_bytes()).hexdigest() == digest, name
    captures = [load(p) for p in sorted(old.glob('capture-[0-9][0-9][0-9][0-9].json'))]
    requests = {}
    for line in (root/'runs/typed-real-dev-v5/pairs.jsonl').read_text().splitlines():
        pair = json.loads(line)
        if pair['learning_split'] == 'development_fit':
            requests.setdefault(pair['uid'], pair)
    desc = load(root/'runs/typed-composer-recovered-128-scorefix-v1/candidate.json')['checkpoint_contract']['prediction_encoding']
    encoding = PredictionCodec(desc['slots'], desc['types'])
    identity = typed_codec.frozen(root/'contracts/typed_codec_v1.json')
    structural, literal = frozen['structural_config'], frozen['literal_config']
    write_new(out/'candidate.json', dict(policy=POLICY, structural_config=structural, literal_config=literal,
              arms=ARMS, decision_ceiling_seconds=2., scope='consumed fit captures; development evidence only',
              design_note='literal-value-v1 was designed after the failure ledger showed these cases\' witness literal differences'))
    solver = []
    started = time.monotonic()
    for capture in captures:
        problem = problem_for(requests[capture['uid']])
        control = run_route('constrained', problem, capture['codes'], capture['logits'], encoding, identity, 0., structural, 2.)
        bitflip = run_semantic_route(control, problem, capture['logits'], encoding, identity, literal, 2.,
                                     literal_filter=unreachable_numeric_guard)
        value = run_semantic_route(control, problem, capture['logits'], encoding, identity, literal, 2.,
                                   literal_filter=unreachable_numeric_guard, literal_policy=literal_value_search)
        solver.append(dict(uid=capture['uid'], routes=dict(control=control, bitflip=bitflip, value=value)))
    write_new(out/'solver-records.json', solver)
    sealed = hashlib.sha256((out/'solver-records.json').read_bytes()).hexdigest()
    write_new(out/'solver-seal.json', dict(solver_records_sha256=sealed))
    rows = []
    for record in solver:
        problem = problem_for(requests[record['uid']])
        tests, _ = development_tests.select(record['uid'], load_hidden_tests(problem))
        assert mine.digest(tests) == requests[record['uid']]['provenance']['independent_tests_sha256']
        row = dict(uid=record['uid'], arms={})
        for arm, route in record['routes'].items():
            scored = score_fixed(route, problem, tests)
            row['arms'][arm] = dict(decision=route['decision'], reason=route['reason'],
                                    accepted_correct=scored['accepted_correct'], wrong_acceptance=scored['wrong_acceptance'],
                                    infrastructure_failure=scored['infrastructure_failure'],
                                    budget_failure=route['reason'] in ('literal_budget', 'semantic_budget', 'decision_budget'),
                                    total_seconds=route['timing']['total_seconds'], **repair_stats(route))
        rows.append(row)
    metrics = {}
    for arm in ARMS:
        rs = [r['arms'][arm] for r in rows]
        metrics[arm] = dict(accepted_correct=sum(r['accepted_correct'] for r in rs),
                            wrong_acceptances=sum(r['wrong_acceptance'] for r in rs),
                            infrastructure_failures=sum(r['infrastructure_failure'] for r in rs),
                            budget_failures=sum(r['budget_failure'] for r in rs),
                            executions=sum(r['executions'] for r in rs),
                            searched_field_edits=sum(r['searched_field_edits'] for r in rs),
                            searched_bit_changes=sum(r['searched_bit_changes'] for r in rs),
                            repair_seconds=round(sum(r['repair_seconds'] for r in rs), 4))
    gained = [r['uid'] for r in rows if r['arms']['value']['accepted_correct'] and not r['arms']['bitflip']['accepted_correct']]
    lost = [r['uid'] for r in rows if r['arms']['bitflip']['accepted_correct'] and not r['arms']['value']['accepted_correct']]
    passes = bool(gained and not lost and metrics['value']['wrong_acceptances'] == 0
                  and metrics['value']['infrastructure_failures'] == 0 and metrics['value']['budget_failures'] == 0)
    report = dict(solver_records_sha256=sealed, metrics=metrics, gained=gained, lost=lost,
                  development_signal=passes, rows=rows, wall_seconds=time.monotonic()-started,
                  limitation='Consumed fit captures; the policy was designed after seeing these failures. Development evidence only.')
    write_new(out/'report.json', report)
    print(json.dumps(dict(metrics=metrics, gained=gained, lost=lost, development_signal=passes), sort_keys=True))


if __name__ == '__main__':
    main()
