"""Step 3 memorization ladder (owner-approved 2026-11-12). Fit targets only.

Frozen before training (written to frozen.json first):
- subsets: S1 = the qualified target with the fewest active slots; S8 = the
  first 8 problems by SHA-256 of their UID; S61 = all 61 problems;
- unchanged from the pilot: TypedPredictor (width 64, 2 layers), the codec
  fitted on all 61 targets (320 slots), per_example_loss with the minimum over
  qualified alternatives, AdamW lr 0.001, full batch, seed 17 (reset per
  subset), the same query embeddings and the same 61-graph retrieval memory;
- cap 4000 steps; evaluation at 400, 1000, 2000 and 4000, all reported; no
  early stopping.
Measured on each subset's own targets: per-head accuracy on active and
padding cells, interior EMPTY, whole-program validity, exact reconstruction,
and public and independent correctness through the sandbox judge.
Held-out rows are never read. Memorization diagnostics, not generalization.

  PYTHONPATH=<pilot tree>/projects/algorithm_solver python memorize.py --build … --dataset … \
      --authorizations … --plan … --out <new dir>
"""
import argparse, hashlib, json, time
from pathlib import Path

import numpy as np
import torch

from algsolve import validate
from algsolve.embed import Embedder
from algsolve.synth import bits_step1, typed_codec
from algsolve.synth import semantic_target_pipeline as pipeline
from algsolve.synth.train_typed import INSTRUCTION, query_text
from algsolve.synth.typed_prediction_codec import PredictionCodec, rejection_details
from algsolve.synth.typed_predictor import TypedPredictor, decisions, per_example_loss

STEPS = (400, 1000, 2000, 4000)
HEADS = ('op', 'first', 'next', 'binding', 'bits')


def main():
    p = argparse.ArgumentParser()
    for name in ('build', 'dataset', 'authorizations', 'plan', 'out'):
        p.add_argument('--' + name, required=True, type=Path)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    pairs = [json.loads(l) for l in (a.build / 'pairs.jsonl').read_text().splitlines()]
    encoding = PredictionCodec.fit(pairs)
    identity = typed_codec.frozen(Path(pipeline.__file__).parents[2] / 'contracts/typed_codec_v1.json')
    uids = list(dict.fromkeys(p['uid'] for p in pairs))
    active = {u: min(sum(1 for v in encoding.encode(p['target']['program'])['op'] if v) for p in pairs if p['uid'] == u) for u in uids}
    s1 = [min(uids, key=lambda u: (active[u], u))]
    s8 = sorted(uids, key=lambda u: hashlib.sha256(u.encode()).hexdigest())[:8]
    subsets = {'S1': s1, 'S8': s8, 'S61': uids}
    frozen = {'subsets': subsets, 'steps': STEPS, 'seed': 17, 'width': 64, 'layers': 2, 'optimizer': 'AdamW',
              'learning_rate': .001, 'loss': 'per_example_loss, minimum over qualified alternatives',
              'codec_slots': encoding.slots, 'retrieval_memory': '61 qualified fit target graphs', 'device': 'cpu', 'threads': 4,
              'pairs_sha256': hashlib.sha256((a.build / 'pairs.jsonl').read_bytes()).hexdigest()}
    (a.out / 'frozen.json').write_text(json.dumps(frozen, indent=1, sort_keys=True))
    torch.set_num_threads(4)

    records, _ = bits_step1.load_authorizations(a.authorizations)
    _, adapter = bits_step1.open_adapter(a.dataset, records)
    plan = pipeline.validate_plan(json.loads(a.plan.read_bytes()))
    adapter.bind_plan(plan)
    rows = {r['uid']: r for r in plan['rows']}
    by_uid = {u: [p for p in pairs if p['uid'] == u] for u in uids}
    embedder = Embedder(device='cpu')
    memory_text = [typed_codec.digest(p['target']) + ' ' + json.dumps(p['target']['program'], sort_keys=True) for p in pairs]
    contracts = embedder.encode(memory_text, batch_size=4)
    vectors = {u: embedder.encode([query_text(by_uid[u][0])], query=True, instruction=INSTRUCTION)[0] for u in uids}
    neighbours = {u: np.argsort(-(contracts @ vectors[u]), kind='stable')[:4] for u in uids}
    problems = {u: adapter.load_problem(rows[u]) for u in uids}
    independent = {}
    results = {}
    for name, subset in subsets.items():
        torch.manual_seed(17)
        sub_pairs = [p for u in subset for p in by_uid[u]]
        labels = {k: torch.tensor([encoding.encode(p['target']['program'])[k] for p in sub_pairs])
                  for k in encoding.encode(sub_pairs[0]['target']['program'])}
        groups = [[j for j, p in enumerate(sub_pairs) if p['uid'] == u] for u in subset]
        query = torch.from_numpy(np.array([vectors[p['uid']] for p in sub_pairs]))
        memory = torch.from_numpy(np.array([contracts[neighbours[p['uid']]] for p in sub_pairs]))
        eval_query = torch.from_numpy(np.array([vectors[u] for u in subset]))
        eval_memory = torch.from_numpy(np.array([contracts[neighbours[u]] for u in subset]))
        model = TypedPredictor(query.shape[1], encoding.slots, len(encoding.types), width=64)
        optimizer = torch.optim.AdamW(model.parameters(), lr=.001)
        started = time.perf_counter(); losses = {}; points = []
        for step in range(1, STEPS[-1] + 1):
            model.train(); optimizer.zero_grad()
            per_target = per_example_loss(model(query, memory), labels)
            loss = torch.stack([per_target[g].min() for g in groups]).mean()
            loss.backward(); optimizer.step()
            if step in STEPS:
                losses[step] = float(loss.detach())
                train_seconds = time.perf_counter() - started
                model.eval()
                with torch.inference_mode():
                    logits = model(eval_query, eval_memory)
                point = {'step': step, 'loss': losses[step], 'train_seconds': train_seconds, 'heads': {}, 'problems': []}
                correct = {h: [0, 0, 0, 0] for h in HEADS}  # active correct/total, padding correct/total
                for i, u in enumerate(subset):
                    predicted = decisions(logits, i)
                    alternatives = [encoding.encode(q['target']['program']) for q in by_uid[u]]
                    label = min(alternatives, key=lambda l: sum(int(x != y) for x, y in zip(predicted['op'], l['op'])))
                    length = sum(1 for v in label['op'] if v)
                    for h in HEADS:
                        for s in range(encoding.slots):
                            t = np.array(label[h][s]); pv = np.array(predicted[h][s])
                            mask = t != -100
                            if not np.any(mask): continue
                            zone = 0 if s < length else 2
                            correct[h][zone] += int(np.sum((pv == t)[mask]) if t.ndim else int(pv == t))
                            correct[h][zone + 1] += int(np.sum(mask) if t.ndim else 1)
                    ops = predicted['op']
                    prefix = next((s for s in range(encoding.slots) if ops[s] == 0), encoding.slots)
                    entry = {'uid': u, 'true_active': length, 'interior_empty': prefix < max([s for s in range(encoding.slots) if ops[s]], default=-1)}
                    params = [x[0] for x in problems[u].params]
                    try:
                        graph = encoding.decode(predicted, params)
                        target = typed_codec.encode(graph, identity)
                        entry['valid'] = True
                        entry['exact_reconstruction'] = any(target['expanded_sha256'] == typed_codec.encode(q['target']['program'], identity)['expanded_sha256'] for q in by_uid[u])
                        source = typed_codec.render(target, identity, method=problems[u].entry['method'], params=params)
                        pub = validate.judge_problem(problems[u], source, problems[u].public_tests)
                        entry['public_correct'] = pub.passed
                        if pub.passed:
                            if u not in independent:
                                independent[u] = adapter.load_independent_tests(rows[u])
                            entry['independent_correct'] = validate.judge_problem(problems[u], source, independent[u]).passed
                    except ValueError as error:
                        entry['valid'] = False; entry['rejection'] = rejection_details(error)['code']
                    point['problems'].append(entry)
                point['heads'] = {h: {'active': round(c[0] / c[1], 4) if c[1] else None,
                                      'padding': round(c[2] / c[3], 4) if c[3] else None} for h, c in correct.items()}
                n = len(subset)
                point['summary'] = {'valid': sum(e['valid'] for e in point['problems']),
                                    'exact_reconstruction': sum(e.get('exact_reconstruction', False) for e in point['problems']),
                                    'public_correct': sum(e.get('public_correct', False) for e in point['problems']),
                                    'independent_correct': sum(e.get('independent_correct', False) for e in point['problems']),
                                    'interior_empty': sum(e['interior_empty'] for e in point['problems']), 'problems': n}
                points.append(point)
                print(json.dumps({'subset': name, 'step': step, 'loss': round(losses[step], 4), 'op_active': point['heads']['op']['active'],
                                  **point['summary'], 'train_seconds': round(train_seconds, 1)}), flush=True)
        results[name] = points
        (a.out / f'{name}.json').write_text(json.dumps(points, indent=1, sort_keys=True))
    (a.out / 'results.json').write_text(json.dumps({'frozen': frozen, 'results': {k: [x['summary'] | {'step': x['step'], 'loss': x['loss'],
                                       'op_active': x['heads']['op']['active'], 'train_seconds': x['train_seconds']} for x in v]
                                       for k, v in results.items()}}, indent=1, sort_keys=True))


if __name__ == '__main__':
    main()
