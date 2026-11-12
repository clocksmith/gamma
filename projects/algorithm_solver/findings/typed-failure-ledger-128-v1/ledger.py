"""Evaluator-isolated failure ledger for the sealed literal-margin fit captures.

Two physically separate phases, joined only after commitment:

1. Solver phase: replay the ten sealed captures through the guard experiment's
   control, semantic and guarded-candidate routes (public inputs, captured
   predictions and logits only) and write the solver records. Their hash is
   sealed before any evaluator data is opened.
2. Evaluator phase: load witness programs (the qualified fit targets),
   independent tests and training exposure; score every route, record
   counterexamples and field differences against the nearest witness, and run
   controlled attribution experiments that substitute one field class of the
   witness into the solver's candidate.

Attribution strength:
  observed           a decode rejection, exception, budget exhaustion or public
                     behavioral disagreement the solver itself recorded;
  controlled_repair  substituting the witness's values for one declared field
                     class makes the candidate independently correct (a
                     sufficient correction in this setting, not a unique cause);
  hypothesis         a difference against the witness whose effect was not
                     isolated.
Witness values never enter the solver phase. Consumed fitting problems only.

  PYTHONPATH=<tree>/projects/algorithm_solver python ledger.py --lane <checkout lane> --out <new dir>
"""
import argparse, copy, hashlib, json
from pathlib import Path

from algsolve.records import load_hidden_tests
from algsolve.synth import typed_codec, development_tests, mine
from algsolve.synth.train_typed import problem_for
from algsolve.synth.typed_prediction_codec import INPUTS, OPS, PredictionCodec, rejection_details
from algsolve.synth.typed_comparison import run_route, score_fixed
from algsolve.synth.typed_semantic_repair import run_semantic_route
from algsolve.synth.typed_guard_filter import unreachable_numeric_guard
from algsolve import validate



def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, indent=1, sort_keys=True) + '\n')


def final_codes(route):
    repair = route.get('semantic_repair') or {}
    if repair.get('final_codes') is not None:
        return repair['final_codes']
    correction = route.get('correction') or {}
    return correction.get('final_codes') or route.get('raw_codes')


def literal_value(bits):
    magnitude = sum(int(b) << k for k, b in enumerate(bits[1:]))
    return -magnitude if bits[0] else magnitude


def differences(solver, witness, params):
    """Meaningful field cells in which the solver codes differ from the witness codes.

    Padding is excluded: operations and structure on slots active on either side,
    bindings on reference/assignment slots of both, literal bits on literal
    slots of both, and types for real parameters and the output only.
    """
    active = [i for i in range(len(solver['op'])) if solver['op'][i] != 0 or witness['op'][i] != 0]
    label = lambda codes, i: OPS[codes['op'][i]] if 0 <= codes['op'][i] < len(OPS) else '?'
    out = {}
    def add(name, cell):
        out.setdefault(name, []).append(cell)
    for i in active:
        if solver['op'][i] != witness['op'][i]:
            add('operation', {'field': 'op', 'slot': i, 'solver': label(solver, i), 'witness': label(witness, i)})
        for field in ('first', 'next'):
            if solver[field][i] != witness[field][i]:
                add('structure', {'field': field, 'slot': i})
        if label(solver, i) in ('ref', 'set') and label(witness, i) in ('ref', 'set') and solver['binding'][i] != witness['binding'][i]:
            add('binding', {'field': 'binding', 'slot': i})
        if label(solver, i) in ('int', 'bool') and label(witness, i) in ('int', 'bool') and solver['bits'][i] != witness['bits'][i]:
            add('literal', {'field': 'bits', 'slot': i, 'solver_value': literal_value(solver['bits'][i]),
                            'witness_value': literal_value(witness['bits'][i]),
                            'bit_changes': sum(a != b for a, b in zip(solver['bits'][i], witness['bits'][i]))})
    for i in [*range(len(params)), INPUTS]:
        if solver['types'][i] != witness['types'][i]:
            add('type', {'field': 'types', 'slot': i})
    return out


def render(graph, identity, problem):
    target = typed_codec.encode(graph, identity)
    return typed_codec.render(target, identity, method=problem.entry['method'], params=[p[0] for p in problem.params])


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
        assert sha_bytes((old/name).read_bytes()) == digest, name
    captures = [load(p) for p in sorted(old.glob('capture-[0-9][0-9][0-9][0-9].json'))]
    pairs = [json.loads(line) for line in (root/'runs/typed-real-dev-v5/pairs.jsonl').read_text().splitlines()]
    requests = {}
    for pair in pairs:
        if pair['learning_split'] == 'development_fit':
            requests.setdefault(pair['uid'], pair)
    assert list(requests) == [c['uid'] for c in captures]
    desc = load(root/'runs/typed-composer-recovered-128-scorefix-v1/candidate.json')['checkpoint_contract']['prediction_encoding']
    encoding = PredictionCodec(desc['slots'], desc['types'])
    identity = typed_codec.frozen(root/'contracts/typed_codec_v1.json')
    structural, literal = frozen['structural_config'], frozen['literal_config']

    # Phase 1: solver records from public inputs and captures only.
    solver = []
    for capture in captures:
        problem = problem_for(requests[capture['uid']])
        control = run_route('constrained', problem, capture['codes'], capture['logits'], encoding, identity, 0., structural, 2.)
        semantic = run_semantic_route(control, problem, capture['logits'], encoding, identity, literal, 2.)
        candidate = run_semantic_route(control, problem, capture['logits'], encoding, identity, literal, 2.,
                                       literal_filter=unreachable_numeric_guard)
        solver.append({'uid': capture['uid'], 'routes': {'control': control, 'semantic': semantic, 'candidate': candidate}})
    write_new(out/'solver-records.json', solver)
    solver_seal = sha_bytes((out/'solver-records.json').read_bytes())
    write_new(out/'solver-seal.json', {'solver_records_sha256': solver_seal,
                                       'note': 'Sealed before witnesses, independent tests or exposure were opened.'})

    # Phase 2: evaluator knowledge, joined after the seal.
    ledger = []
    for record in solver:
        uid = record['uid']
        problem = problem_for(requests[uid])
        tests, _ = development_tests.select(uid, load_hidden_tests(problem))
        assert mine.digest(tests) == requests[uid]['provenance']['independent_tests_sha256']
        witnesses = []
        for pair in pairs:
            if pair['uid'] != uid or pair['learning_split'] != 'development_fit':
                continue
            entry = {'variant': pair['variant'], 'graph_sha256': pair['graph_sha256']}
            try:
                entry['codes'] = encoding.encode(pair['target']['program'])
                entry['encoding'] = 'fits_frozen_encoding'
            except ValueError as error:
                entry['encoding'] = 'outside_frozen_encoding: ' + str(error)
            witnesses.append(entry)
        row = {'uid': uid, 'evidence': {
            'witnesses': [{k: v for k, v in w.items() if k != 'codes'} for w in witnesses],
            'training_exposure': {'in_training_fit': True, 'qualified_alternatives': len(witnesses),
                                  'per_alternative_contribution': 'unknown (not retained by the historical training run)'},
            'independent_tests': len(tests)}, 'routes': {}}
        for name, route in record['routes'].items():
            scored = score_fixed(route, problem, tests)
            verdict = scored['independent'] or {}
            entry = {'decision': route['decision'], 'reason': route['reason'],
                     'independently_correct': scored['independently_correct'],
                     'accepted_correct': scored['accepted_correct'], 'wrong_acceptance': scored['wrong_acceptance'],
                     'counterexample': verdict.get('detail') if verdict and not verdict.get('passed') else None,
                     'observed': [], 'controlled_repairs': [], 'hypotheses': []}
            # Observed: what the solver itself recorded.
            for stage in route.get('stages', []):
                if stage['stage'] == 'decode' and stage.get('details'):
                    entry['observed'].append({'kind': 'decode_rejection', **stage['details']})
                if stage['stage'] == 'correction' and stage.get('details'):
                    entry['observed'].append({'kind': 'raw_rejection_before_correction', **stage['details']})
                if stage['stage'] == 'public_check' and stage['outcome'] == 'public_failure':
                    entry['observed'].append({'kind': 'public_behavior_disagreement',
                                              'public_detail': (route['public'] or {}).get('detail')})
                if stage['stage'] == 'budget_override':
                    entry['observed'].append({'kind': 'budget_exhausted', 'overridden': stage['overridden_reason']})
            for key in ('semantic_stage', 'literal_stage'):
                if (route.get(key) or {}).get('budget_override'):
                    entry['observed'].append({'kind': 'budget_exhausted', 'stage': key, 'which': route[key]['budget_override']})
            if not entry['accepted_correct']:
                codes = final_codes(route)
                fitting = [w for w in witnesses if 'codes' in w]
                if codes is not None and fitting:
                    params = [p[0] for p in problem.params]
                    nearest = min(fitting, key=lambda w: sum(len(c) for c in differences(codes, w['codes'], params).values()))
                    diff = differences(codes, nearest['codes'], params)
                    entry['nearest_witness'] = nearest['variant']
                    entry['differences'] = {k: len(v) for k, v in diff.items()}
                    entry['literal_differences'] = diff.get('literal', [])
                    entry['operation_differences'] = diff.get('operation', [])
                    for cls, cells in diff.items():
                        trial = copy.deepcopy(codes)
                        for cell in cells:
                            trial[cell['field']][cell['slot']] = copy.deepcopy(nearest['codes'][cell['field']][cell['slot']])
                        outcome = {'field_class': cls, 'cells': len(cells)}
                        try:
                            graph = encoding.decode(trial, [p[0] for p in problem.params])
                            verdict = validate.judge_problem(problem, render(graph, identity, problem), tests).to_dict()
                            outcome['independently_correct'] = verdict['passed']
                        except ValueError as error:
                            outcome['rejected'] = rejection_details(error)
                        (entry['controlled_repairs'] if outcome.get('independently_correct') else entry['hypotheses']).append(outcome)
            row['routes'][name] = entry
        ledger.append(row)
    write_new(out/'evaluator-ledger.json', {'solver_records_sha256': solver_seal, 'rows': ledger})
    summary = {route: {'accepted_correct': sum(r['routes'][route]['accepted_correct'] for r in ledger),
                       'wrong_acceptances': sum(r['routes'][route]['wrong_acceptance'] for r in ledger),
                       'abstained_but_independently_correct': sum(r['routes'][route]['decision'] == 'abstain'
                                                                   and r['routes'][route]['independently_correct'] is True for r in ledger),
                       'controlled_repairs_by_class': {}}
               for route in ('control', 'semantic', 'candidate')}
    for r in ledger:
        for route, entry in r['routes'].items():
            for repair in entry['controlled_repairs']:
                counts = summary[route]['controlled_repairs_by_class']
                counts[repair['field_class']] = counts.get(repair['field_class'], 0) + 1
    print(json.dumps({'solver_records_sha256': solver_seal, 'summary': summary}, sort_keys=True))


if __name__ == '__main__':
    main()
