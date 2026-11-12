"""One proposal family at a time after the guarded semantic route.

Arms (identical shared budgets: recipe, literal and family stages share
.25 s and 4 public executions within the 2 s ceiling; guard filter on all):
  control     guarded semantic route (recipe, then bit-flip literal)
  operation   control + pure-operation substitution
  binding     control + same-type binding rewiring
Settings:
  mutants   the eight authored task/mutant repair requests (distinguishing
            example added; synthetic uniform logits), scored on the finite
            domain from ../typed-mutant-diagnostics-v1
  captures  the ten sealed literal-margin fit captures (real logits); solver
            records sealed before independent tests are loaded

  PYTHONPATH=<tree>/projects/algorithm_solver python run_families.py --lane <checkout lane> --out <new dir>
"""
import argparse, hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / 'typed-mutant-diagnostics-v1'))
import run_mutants as M  # noqa: E402

from algsolve.records import load_hidden_tests
from algsolve.synth import typed_codec, development_tests, mine
from algsolve.synth.train_typed import problem_for
from algsolve.synth.typed_prediction_codec import PredictionCodec
from algsolve.synth.typed_comparison import run_route, score_fixed
from algsolve.synth.typed_semantic_repair import run_semantic_route
from algsolve.synth.typed_guard_filter import unreachable_numeric_guard

ARMS = {'control': None, 'operation': 'operation', 'binding': 'binding'}


def arms_for(control, problem, logits, encoding, identity, literal):
    return {name: run_semantic_route(control, problem, logits, encoding, identity, literal, 2.,
                                     literal_filter=unreachable_numeric_guard, followup_family=family)
            for name, family in ARMS.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lane', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    root, out = args.lane, args.out
    out.mkdir(parents=True, exist_ok=False)
    load = lambda p: json.loads(Path(p).read_text())
    desc = load(root/'runs/typed-composer-recovered-128-scorefix-v1/candidate.json')['checkpoint_contract']['prediction_encoding']
    encoding = PredictionCodec(desc['slots'], desc['types'])
    identity = typed_codec.frozen(root/'contracts/typed_codec_v1.json')
    old = root/'runs/typed-literal-margin-fit-128-v1'
    frozen = load(old/'candidate.json')
    structural, literal = frozen['structural_config'], frozen['literal_config']

    # Mutant repair requests.
    pairs = load(HERE.parent/'typed-mutant-diagnostics-v1/pairs.json')['pairs']
    mutant_rows = []
    for pair in pairs:
        inputs = list(M.domain(pair))
        expected = [M.run(pair['correct'], x) for x in inputs]
        mutant_out = [M.run(pair['mutant'], x) for x in inputs]
        agree = [i for i, (a, b) in enumerate(zip(expected, mutant_out)) if a == b]
        tests = ([{'inputs': inputs[agree[0]], 'expected': expected[agree[0]]}] if agree else []) + [
            {'inputs': pair['distinguishing_example']['inputs'], 'expected': pair['distinguishing_example']['expected']}]
        params = pair['correct']['parameters']
        codes = encoding.encode(pair['mutant'])
        codes = {k: [[0 if b == -100 else b for b in v] if isinstance(v, list) else (0 if v == -100 else v) for v in vals]
                 for k, vals in codes.items()}
        logits = M.synthetic_logits(encoding, codes)
        prob = M.problem(pair, tests)
        control = run_route('constrained', prob, codes, logits, encoding, identity, 0., structural, 2.)
        row = {'id': pair['id'], 'mutation_class': pair['mutation_class'], 'arms': {}}
        for name, route in arms_for(control, prob, logits, encoding, identity, literal).items():
            graph = route['final_graph']
            correct = graph is not None and all(M.run(graph, x) == e for x, e in zip(inputs, expected))
            family = (route.get('semantic_repair') or {}).get('family_repair') or {}
            row['arms'][name] = {'decision': route['decision'], 'reason': route['reason'],
                                 'accepted_correct': route['decision'] == 'answered' and correct,
                                 'wrong_acceptance': route['decision'] == 'answered' and not correct,
                                 'edits': (route.get('semantic_repair') or {}).get('edits'),
                                 'family_executions': family.get('executions', 0),
                                 'executions': (route.get('semantic_repair') or {}).get('executions', 0)}
        mutant_rows.append(row)

    # Sealed real captures.
    captures = [load(p) for p in sorted(old.glob('capture-[0-9][0-9][0-9][0-9].json'))]
    for name, digest in load(old/'capture-seal.json')['captures_sha256'].items():
        assert hashlib.sha256((old/name).read_bytes()).hexdigest() == digest, name
    requests = {}
    for line in (root/'runs/typed-real-dev-v5/pairs.jsonl').read_text().splitlines():
        pair = json.loads(line)
        if pair['learning_split'] == 'development_fit':
            requests.setdefault(pair['uid'], pair)
    solver = []
    for capture in captures:
        problem = problem_for(requests[capture['uid']])
        control = run_route('constrained', problem, capture['codes'], capture['logits'], encoding, identity, 0., structural, 2.)
        solver.append({'uid': capture['uid'], 'routes': arms_for(control, problem, capture['logits'], encoding, identity, literal)})
    (out/'solver-records.json').write_text(json.dumps(solver, sort_keys=True))
    sealed = hashlib.sha256((out/'solver-records.json').read_bytes()).hexdigest()
    capture_rows = []
    for record in solver:
        problem = problem_for(requests[record['uid']])
        tests, _ = development_tests.select(record['uid'], load_hidden_tests(problem))
        assert mine.digest(tests) == requests[record['uid']]['provenance']['independent_tests_sha256']
        row = {'uid': record['uid'], 'arms': {}}
        for name, route in record['routes'].items():
            scored = score_fixed(route, problem, tests)
            row['arms'][name] = {'decision': route['decision'], 'reason': route['reason'],
                                 'accepted_correct': scored['accepted_correct'], 'wrong_acceptance': scored['wrong_acceptance'],
                                 'executions': (route.get('semantic_repair') or {}).get('executions', 0)}
        capture_rows.append(row)

    def metrics(rows):
        return {arm: {'accepted_correct': sum(r['arms'][arm]['accepted_correct'] for r in rows),
                      'wrong_acceptances': sum(r['arms'][arm]['wrong_acceptance'] for r in rows),
                      'executions': sum(r['arms'][arm]['executions'] for r in rows),
                      'lost_vs_control': [r.get('id', r.get('uid')) for r in rows
                                          if r['arms']['control']['accepted_correct'] and not r['arms'][arm]['accepted_correct']],
                      'gained_vs_control': [r.get('id', r.get('uid')) for r in rows
                                            if r['arms'][arm]['accepted_correct'] and not r['arms']['control']['accepted_correct']]}
                for arm in ARMS}
    report = {'solver_records_sha256': sealed, 'mutants': {'metrics': metrics(mutant_rows), 'rows': mutant_rows},
              'captures': {'metrics': metrics(capture_rows), 'rows': capture_rows},
              'scope': 'Mutants: authored fixtures with synthetic logits. Captures: consumed fit problems. Development evidence only.'}
    (out/'report.json').write_text(json.dumps(report, indent=1, sort_keys=True))
    print(json.dumps({'mutants': report['mutants']['metrics'], 'captures': report['captures']['metrics']}, sort_keys=True))


if __name__ == '__main__':
    main()
