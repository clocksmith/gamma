"""Detection and repair diagnostics on the eight authored task/mutant pairs.

The pairs (pairs.json, gamma.authored-mutant-diagnostics.v1) are synthetic
authored fixtures, not training targets, protected evaluation or model results.

For each pair:
- Scoring domain: every input of the task's stated domain (M02: all lists of
  0-3 pairs with components in -2..2, a bounded sub-domain authored here).
  Outputs come from the authored correct graph through the IR interpreter.
- Weak public example: the first domain input on which correct and mutant
  agree. Detection request: that example only. A mutant accepted under it is
  weak evidence, not a route defect.
- Repair request: a separately frozen request adding the distinguishing
  example. Starting from the mutant's encoding, the constrained route and the
  existing recipe-then-bit-flip repair run with the standard budgets.
- Logits are synthetic: every recorded decision scores 1.0 and alternatives
  0.0; literal bits score +1/-1. Repair order therefore reflects reachability
  under uniform margins, not a model's ranking.
- Neighbourhood: the meaningful field cells separating mutant from correct,
  and whether an existing repair family (recipe swap; one or two literal bit
  flips) can cover them.

  PYTHONPATH=<tree>/projects/algorithm_solver python run_mutants.py --lane <checkout lane> --out <new dir>
"""
import argparse, itertools, json
from pathlib import Path

from algsolve.records import Problem
from algsolve.synth import typed_codec, typed_program as ir
from algsolve.synth.typed_prediction_codec import INPUTS, OPS, PredictionCodec, rejection_details
from algsolve.synth.typed_comparison import run_route
from algsolve.synth.typed_semantic_repair import run_semantic_route

HERE = Path(__file__).parent
INT = range(-100, 101)


def domain(pair):
    names = pair['correct']['parameters']
    if pair['id'] == 'M02':
        values = [[a, b] for a in range(-2, 3) for b in range(-2, 3)]
        for length in range(4):
            for items in itertools.product(values, repeat=length):
                yield {'xs': [list(v) for v in items]}
        return
    if pair['id'] == 'M07':
        for n in range(1, 101):
            yield {'n': n}
        return
    for combo in itertools.product(INT, repeat=len(names)):
        yield dict(zip(names, combo))


def run(graph, inputs):
    return json.loads(json.dumps(ir.execute(graph, inputs)))


def annotation(t):
    if t == 'int':
        return 'int'
    if t == 'bool':
        return 'bool'
    return 'List[List[int]]' if t == ['list', ['tuple', 'int', 'int']] else 'List[int]'


def problem(pair, tests):
    g = pair['correct']
    params = [[n, annotation(g['inputs'][n])] for n in g['parameters']]
    return Problem(uid='mutant:' + pair['id'], source='synthetic', source_id=pair['id'], title=pair['id'], slug='',
                   statement=pair['task'], io_mode='functional', entry={'class': 'Solution', 'method': 'solve'},
                   params=params, license='authored diagnostic', attribution='gamma.authored-mutant-diagnostics.v1',
                   evidence_ceiling='independent_tests_passed',
                   public_tests=[{'args': [t['inputs'][n] for n in g['parameters']], 'expected': t['expected']} for t in tests])


def synthetic_logits(encoding, codes):
    def onehot(values, width):
        return [[1.0 if j == int(v) else 0.0 for j in range(width)] for v in values]
    return {'op': onehot(codes['op'], len(OPS)), 'first': onehot(codes['first'], encoding.slots + 1),
            'next': onehot(codes['next'], encoding.slots + 1), 'binding': onehot(codes['binding'], INPUTS + encoding.slots),
            'types': onehot(codes['types'], len(encoding.types)),
            'bits': [[1.0 if b else -1.0 for b in row] for row in codes['bits']]}


def neighbourhood(mutant, correct, params):
    label = lambda c, i: OPS[c['op'][i]]
    active = [i for i in range(len(mutant['op'])) if mutant['op'][i] or correct['op'][i]]
    cells = []
    for i in active:
        if mutant['op'][i] != correct['op'][i]:
            cells.append({'class': 'operation', 'slot': i, 'mutant': label(mutant, i), 'correct': label(correct, i)})
        for f in ('first', 'next'):
            if mutant[f][i] != correct[f][i]:
                cells.append({'class': 'structure', 'slot': i, 'field': f})
        if label(mutant, i) in ('ref', 'set') and label(correct, i) in ('ref', 'set') and mutant['binding'][i] != correct['binding'][i]:
            cells.append({'class': 'binding', 'slot': i})
        if label(mutant, i) in ('int', 'bool') and label(correct, i) in ('int', 'bool') and mutant['bits'][i] != correct['bits'][i]:
            cells.append({'class': 'literal', 'slot': i, 'bit_changes': sum(a != b for a, b in zip(mutant['bits'][i], correct['bits'][i]))})
    for i in [*range(len(params)), INPUTS]:
        if mutant['types'][i] != correct['types'][i]:
            cells.append({'class': 'type', 'slot': i})
    classes = sorted({c['class'] for c in cells})
    literal_bits = sum(c.get('bit_changes', 0) for c in cells)
    recipe_only = classes == ['operation'] and all(c['mutant'].startswith('recipe:') and c['correct'].startswith('recipe:') for c in cells)
    covered = (classes == ['literal'] and literal_bits <= 2) or (recipe_only and len(cells) == 1)
    return cells, classes, covered


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lane', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    pairs = json.loads((HERE / 'pairs.json').read_text())
    desc = json.loads((args.lane / 'runs/typed-composer-recovered-128-scorefix-v1/candidate.json').read_text())['checkpoint_contract']['prediction_encoding']
    encoding = PredictionCodec(desc['slots'], desc['types'])
    identity = typed_codec.frozen(args.lane / 'contracts/typed_codec_v1.json')
    frozen = json.loads((args.lane / 'runs/typed-literal-margin-fit-128-v1/candidate.json').read_text())
    structural, literal = frozen['structural_config'], frozen['literal_config']
    rows = []
    for pair in pairs['pairs']:
        inputs = list(domain(pair))
        expected = [run(pair['correct'], x) for x in inputs]
        mutant_out = [run(pair['mutant'], x) for x in inputs]
        agree = [i for i, (a, b) in enumerate(zip(expected, mutant_out)) if a == b]
        weak = {'inputs': inputs[agree[0]], 'expected': expected[agree[0]]} if agree else None
        distinguishing = {'inputs': pair['distinguishing_example']['inputs'], 'expected': pair['distinguishing_example']['expected']}
        row = {'id': pair['id'], 'mutation_class': pair['mutation_class'], 'domain_inputs': len(inputs),
               'mutant_domain_accuracy': len(agree) / len(inputs), 'weak_public_example': weak}
        params = pair['correct']['parameters']
        try:
            codes = {k: encoding.encode(pair[k]) for k in ('correct', 'mutant')}
        except ValueError as error:
            row['encoding'] = 'outside_frozen_encoding: ' + str(error)
            rows.append(row)
            continue
        row['encoding'] = 'fits_frozen_encoding'
        cells, classes, covered = neighbourhood(codes['mutant'], codes['correct'], params)
        # A model capture holds a decision in every cell; encode() pads unused cells
        # with -100. The synthetic prediction takes decision 0 there, as an argmax
        # over the uniform synthetic logits would, and must decode to the mutant.
        codes['mutant'] = {k: [[0 if b == -100 else b for b in v] if isinstance(v, list) else (0 if v == -100 else v)
                               for v in values] for k, values in codes['mutant'].items()}
        if typed_codec.digest(encoding.decode(codes['mutant'], params)) != typed_codec.digest(
                encoding.decode(encoding.encode(pair['mutant']), params)):
            raise ValueError('Synthetic prediction does not decode to the mutant')
        row['neighbourhood'] = {'cells': cells, 'classes': classes, 'covered_by_existing_repair': covered}
        logits = synthetic_logits(encoding, codes['mutant'])
        def score(graph):
            return graph is not None and all(run(graph, x) == e for x, e in zip(inputs, expected))
        for name, tests in (('detection', [weak] if weak else []), ('repair', [t for t in (weak, distinguishing) if t])):
            prob = problem(pair, tests)
            control = run_route('constrained', prob, codes['mutant'], logits, encoding, identity, 0., structural, 2.)
            repaired = run_semantic_route(control, prob, logits, encoding, identity, literal, 2.)
            entry = {}
            for arm, route in (('control', control), ('repaired', repaired)):
                graph = route['final_graph']
                correct = score(graph)
                entry[arm] = {'decision': route['decision'], 'reason': route['reason'],
                              'finite_domain_correct': correct,
                              'wrong_acceptance': route['decision'] == 'answered' and not correct,
                              'accepted_correct': route['decision'] == 'answered' and correct}
            literal_repair = ((repaired.get('semantic_repair') or {}).get('literal_repair') or {})
            entry['repaired']['literal_attempts'] = len(literal_repair.get('attempts', []))
            entry['repaired']['executions'] = (repaired.get('semantic_repair') or {}).get('executions', 0)
            row[name] = entry
        rows.append(row)
    report = {'schema': 'gamma.authored-mutant-diagnostics-report.v1', 'source_pairs_schema': pairs['schema'],
              'pairs_runtime_source_sha256': pairs['runtime_source_sha256'], 'rows': rows,
              'scope': 'Authored synthetic diagnostics with synthetic uniform logits; engineering evidence about '
                       'detection and repair reachability, not model or generalization evidence.'}
    (args.out / 'report.json').write_text(json.dumps(report, indent=1, sort_keys=True))
    for row in rows:
        n = row.get('neighbourhood', {})
        print(row['id'], row['mutation_class'], '| enc', row['encoding'][:22], '| mutant acc %.3f' % row['mutant_domain_accuracy'],
              '| classes', n.get('classes'), 'covered', n.get('covered_by_existing_repair'),
              '| detect', {k: (v['decision'], v['finite_domain_correct']) for k, v in row.get('detection', {}).items() if isinstance(v, dict)},
              '| repair', {k: (v['decision'], v['finite_domain_correct']) for k, v in row.get('repair', {}).items() if isinstance(v, dict)})


if __name__ == '__main__':
    main()
