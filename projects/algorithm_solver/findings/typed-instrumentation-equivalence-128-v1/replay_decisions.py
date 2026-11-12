"""Replay the sealed literal-margin fit captures through the guard experiment's routes
and print canonical public decisions, without independent tests or scoring.

Run with PYTHONPATH set to the source tree under test, so the baseline and the
instrumented trees replay the same captures with the same driver:

  PYTHONPATH=<tree>/projects/algorithm_solver python replay_decisions.py --lane <checkout lane> --out <file>

The canonical record keeps only fields present before instrumentation: decision,
reason, candidate graph hash, public verdict, and the ordered correction,
recipe and literal attempts. Timings are reported separately.
"""
import argparse, hashlib, json, time
from pathlib import Path

from algsolve.synth import typed_codec
from algsolve.synth.train_typed import problem_for
from algsolve.synth.typed_prediction_codec import PredictionCodec
from algsolve.synth.typed_comparison import run_route
from algsolve.synth.typed_semantic_repair import run_semantic_route
from algsolve.synth.typed_guard_filter import unreachable_numeric_guard


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def attempts(repair):
    return [dict(edits=a['edits'], validation_failure=a['validation_failure'],
                 proposal_filter_failure=a.get('proposal_filter_failure'),
                 graph_sha256=a.get('graph_sha256'),
                 public_passed=(a['public'] or {}).get('passed'), public_reason=(a['public'] or {}).get('reason'))
            for a in (repair or {}).get('attempts', [])]


def canonical(route):
    correction = route.get('correction') or {}
    semantic = route.get('semantic_repair') or {}
    literal = semantic.get('literal_repair') or {}
    return dict(decision=route['decision'], reason=route['reason'], graph_sha256=route['graph_sha256'],
                structurally_valid=route['structurally_valid'], infrastructure_failure=route['infrastructure_failure'],
                public_passed=(route['public'] or {}).get('passed'), public_reason=(route['public'] or {}).get('reason'),
                correction=dict(reason=correction.get('reason'), edits=correction.get('edits'),
                                attempts=[dict(edits=a['edits'], validation_failure=a['validation_failure'])
                                          for a in correction.get('attempts', [])]),
                semantic=dict(pool=semantic.get('pool'), reason=semantic.get('reason'), edits=semantic.get('edits'),
                              executions=semantic.get('executions'), attempts=attempts(semantic)),
                literal=dict(pool=literal.get('pool'), reason=literal.get('reason'), executions=literal.get('executions')))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lane', required=True, type=Path, help='checkout lane holding runs/ and contracts/')
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    root = args.lane
    old = root/'runs/typed-literal-margin-fit-128-v1'
    load = lambda p: json.loads(Path(p).read_text())
    frozen = load(old/'candidate.json')
    seal = load(old/'capture-seal.json')
    for name, digest in seal['captures_sha256'].items():
        assert sha(old/name) == digest, name
    captures = [load(p) for p in sorted(old.glob('capture-[0-9][0-9][0-9][0-9].json'))]
    unique = {}
    for line in (root/'runs/typed-real-dev-v5/pairs.jsonl').read_text().splitlines():
        pair = json.loads(line)
        if pair['learning_split'] == 'development_fit':
            unique.setdefault(pair['uid'], pair)
    requests = list(unique.values())
    assert [p['uid'] for p in requests] == [c['uid'] for c in captures]
    desc = load(root/'runs/typed-composer-recovered-128-scorefix-v1/candidate.json')['checkpoint_contract']['prediction_encoding']
    encoding = PredictionCodec(desc['slots'], desc['types'])
    identity = typed_codec.frozen(root/'contracts/typed_codec_v1.json')
    structural, literal = frozen['structural_config'], frozen['literal_config']
    rows, timings = [], []
    for pair, capture in zip(requests, captures):
        problem = problem_for(pair)
        started = time.perf_counter()
        control = run_route('constrained', problem, capture['codes'], capture['logits'], encoding, identity, 0., structural, 2.)
        semantic = run_semantic_route(control, problem, capture['logits'], encoding, identity, literal, 2.)
        candidate = run_semantic_route(control, problem, capture['logits'], encoding, identity, literal, 2.,
                                       literal_filter=unreachable_numeric_guard)
        timings.append(dict(uid=pair['uid'], replay_seconds=time.perf_counter()-started,
                            totals={k: r['timing']['total_seconds'] for k, r in
                                    (('control', control), ('semantic', semantic), ('candidate', candidate))}))
        rows.append(dict(uid=pair['uid'], routes={k: canonical(r) for k, r in
                                                  (('control', control), ('semantic', semantic), ('candidate', candidate))}))
    body = json.dumps(rows, sort_keys=True)
    args.out.write_text(json.dumps(dict(decisions_sha256=hashlib.sha256(body.encode()).hexdigest(), rows=rows,
                                        timings=timings), indent=1, sort_keys=True))
    print(json.dumps(dict(decisions_sha256=hashlib.sha256(body.encode()).hexdigest(),
                          decisions={r['uid']: {k: v['decision'] + ':' + str(v['reason']) for k, v in r['routes'].items()} for r in rows})))


if __name__ == '__main__':
    main()
