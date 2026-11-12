"""Memorization diagnostics on the pilot checkpoint, fit targets only. No training.

  PYTHONPATH=<pilot tree>/projects/algorithm_solver python diagnose_fit.py \
      --run <runs/bits-pilot-…> --build <target build> --dataset … --authorizations … --plan … --out <json>

1. Round trip: each qualified target through the exact training codec (encode,
   decode, re-encode to the same expanded hash) and the interpreter on its
   public examples; the codec descriptor equals the pilot contract's; the query
   text built for training equals the one built from the adapter at inference.
2. The checkpoint on its own 61 training queries (training retrieval
   neighbours): per-head accuracy on active vs padding cells against the
   nearest qualified alternative, root validity, interior EMPTY slots,
   predicted vs true active length, whole-program validity, and each head's
   loss split between active and padding cells.
Held-out rows are not read.
"""
import argparse, collections, json
from pathlib import Path

import numpy as np
import torch
from torch import nn

from algsolve.embed import Embedder
from algsolve.judge.judge import values_equal
from algsolve.synth import bits_step1, typed_codec, typed_program as ir, typed_recipes
from algsolve.synth import semantic_target_pipeline as pipeline
from algsolve.synth.train_typed import INSTRUCTION, query_text
from algsolve.synth.typed_prediction_codec import OPS, PredictionCodec, rejection_details
from algsolve.synth.typed_predictor import TypedPredictor, decisions

HEADS = ('op', 'first', 'next', 'binding', 'bits', 'types')


def main():
    p = argparse.ArgumentParser()
    for name in ('run', 'build', 'dataset', 'authorizations', 'plan', 'out'):
        p.add_argument('--' + name, required=True, type=Path)
    a = p.parse_args()
    pairs = [json.loads(l) for l in (a.build / 'pairs.jsonl').read_text().splitlines()]
    contract = json.loads((a.run / 'contract.json').read_text())
    encoding = PredictionCodec.fit(pairs)
    report = {'descriptor_matches_contract': encoding.descriptor() == contract['prediction_encoding'],
              'slots': encoding.slots, 'targets': len(pairs)}
    identity = typed_codec.frozen(Path(pipeline.__file__).parents[2] / 'contracts/typed_codec_v1.json')

    # 1. Round trip and execution.
    round_trip = []
    for pair in pairs:
        program = pair['target']['program']
        entry = {'uid': pair['uid'], 'variant': pair['variant']}
        try:
            codes = encoding.encode(program)
            decoded = encoding.decode(codes, program['parameters'])
            entry['active_slots'] = sum(1 for v in codes['op'] if v != 0)
            entry['same_expanded_hash'] = (typed_codec.encode(decoded, identity)['expanded_sha256']
                                           == typed_codec.encode(program, identity)['expanded_sha256'])
            ok = True
            for example in pair['input']['public_examples']:
                args = dict(zip(program['parameters'], example['args']))
                got = json.loads(json.dumps(ir.execute(decoded, args)))
                ok &= values_equal(example['expected'], got)
            entry['public_examples_reproduced'] = ok
        except Exception as error:
            entry['error'] = f'{type(error).__name__}: {error}'
        round_trip.append(entry)
    report['round_trip'] = {'all_same_hash': all(e.get('same_expanded_hash') for e in round_trip),
                            'all_public_reproduced': all(e.get('public_examples_reproduced') for e in round_trip),
                            'failures': [e for e in round_trip if not (e.get('same_expanded_hash') and e.get('public_examples_reproduced'))],
                            'active_slots': {'min': min(e.get('active_slots', 0) for e in round_trip),
                                             'median': float(np.median([e.get('active_slots', 0) for e in round_trip])),
                                             'max': max(e.get('active_slots', 0) for e in round_trip)}}

    # Query equivalence: training text vs inference text from the adapter.
    records, _ = bits_step1.load_authorizations(a.authorizations)
    _, adapter = bits_step1.open_adapter(a.dataset, records)
    plan = pipeline.validate_plan(json.loads(a.plan.read_bytes()))
    adapter.bind_plan(plan)
    rows = {r['uid']: r for r in plan['rows']}
    fit_uids = list(dict.fromkeys(p['uid'] for p in pairs))
    by_uid = {p['uid']: p for p in pairs}
    mismatched = []
    for uid in fit_uids:
        problem = adapter.load_problem(rows[uid])
        inference = {'input': pipeline._public_input(problem)}
        if query_text(by_uid[uid]) != query_text(inference):
            mismatched.append(uid)
    report['query_text_identical'] = {'checked': len(fit_uids), 'mismatched': mismatched}

    # 2. Checkpoint on its own training queries.
    checkpoint = torch.load(a.run / 'model.pt', map_location='cpu', weights_only=True)
    embedder = Embedder(device='cpu')
    memory_text = [typed_codec.digest(p['target']) + ' ' + json.dumps(p['target']['program'], sort_keys=True) for p in pairs]
    contracts = embedder.encode(memory_text, batch_size=4)
    vectors = np.array([embedder.encode([query_text(by_uid[u])], query=True, instruction=INSTRUCTION)[0] for u in fit_uids])
    neighbours = np.array([np.argsort(-(contracts @ v), kind='stable')[:4] for v in vectors])
    model = TypedPredictor(vectors.shape[1], encoding.slots, len(encoding.types), width=contract['config']['width'])
    model.load_state_dict(checkpoint['state_dict']); model.eval()
    with torch.inference_mode():
        logits = model(torch.from_numpy(vectors), torch.from_numpy(contracts[neighbours]))
    acc = {h: collections.Counter() for h in HEADS}
    loss_split = {h: collections.Counter() for h in HEADS}
    shape = collections.Counter(); counterexamples = []
    for i, uid in enumerate(fit_uids):
        predicted = decisions(logits, i)
        alternatives = [encoding.encode(p['target']['program']) for p in pairs if p['uid'] == uid]
        def errors(label):
            return sum(int(x != y) for x, y in zip(np.ravel(predicted['op']), np.ravel(label['op'])))
        label = min(alternatives, key=errors)
        active = [s for s in range(encoding.slots) if label['op'][s] != 0]
        length = len(active)
        for h in HEADS:
            pred, true = np.array(predicted[h]), np.array(label[h])
            if h == 'types':
                mask = true != -100
                acc[h]['correct'] += int((pred[mask] == true[mask]).sum()); acc[h]['total'] += int(mask.sum())
                continue
            for s in range(encoding.slots):
                zone = 'active' if s < length else 'padding'
                t = true[s]
                if h == 'bits':
                    m = t != -100
                    if not m.any(): continue
                    acc[h][zone + '_correct'] += int((pred[s][m] == t[m]).sum()); acc[h][zone + '_total'] += int(m.sum())
                elif t != -100:
                    acc[h][zone + '_correct'] += int(pred[s] == t); acc[h][zone + '_total'] += 1
            # Loss contributions per zone, matching per_example_loss's per-head mean.
            lt = torch.tensor(label[h])
            pr = logits[h][i]
            if h == 'bits':
                raw = nn.functional.binary_cross_entropy_with_logits(pr, lt.clamp_min(0).float(), reduction='none').sum(-1)
                mask = (lt != -100).any(-1)
            else:
                raw = nn.functional.cross_entropy(pr, lt.clamp_min(0), reduction='none')
                mask = lt != -100
            denom = max(int(mask.sum()), 1)
            loss_split[h]['active'] += float((raw[:length] * mask[:length]).sum()) / denom
            loss_split[h]['padding'] += float((raw[length:] * mask[length:]).sum()) / denom
        ops = predicted['op']
        predicted_active = [s for s in range(encoding.slots) if ops[s] != 0]
        prefix = next((s for s in range(encoding.slots) if ops[s] == 0), encoding.slots)
        shape['root_valid'] += int(OPS[ops[0]] == 'root' and predicted['next'][0] == 0)
        shape['interior_empty_targets'] += int(prefix < max(predicted_active, default=-1))
        shape['shorter_than_true'] += int(prefix < length)
        try:
            encoding.decode(predicted, by_uid[uid]['target']['program']['parameters'])
            shape['valid'] += 1
        except ValueError as error:
            shape['rejection:' + rejection_details(error)['code']] += 1
        if len(counterexamples) < 6:
            first_wrong = next((s for s in range(length) if ops[s] != label['op'][s]), None)
            counterexamples.append({'uid': uid, 'true_active_slots': length, 'predicted_empty_prefix_end': prefix,
                                    'predicted_active_slots': len(predicted_active), 'first_wrong_op_slot': first_wrong,
                                    'true_op_there': OPS[label['op'][first_wrong]] if first_wrong is not None else None,
                                    'predicted_op_there': OPS[ops[first_wrong]] if first_wrong is not None else None})
    n = len(fit_uids)
    report['per_head_accuracy'] = {h: {k: (round(c[k + '_correct'] / c[k + '_total'], 4) if c[k + '_total'] else None)
                                       for k in ('active', 'padding')} if h != 'types'
                                   else round(c['correct'] / max(c['total'], 1), 4) for h, c in acc.items()}
    report['loss_share_by_zone'] = {h: {k: round(v / n, 4) for k, v in c.items()} for h, c in loss_split.items()}
    report['shape'] = dict(shape)
    report['counterexamples'] = counterexamples
    a.out.write_text(json.dumps(report, indent=1, sort_keys=True))
    print(json.dumps({k: report[k] for k in ('descriptor_matches_contract', 'slots', 'query_text_identical', 'per_head_accuracy',
                                              'loss_share_by_zone', 'shape')}, indent=1))
    print(json.dumps({k: v for k, v in report['round_trip'].items() if k != 'failures'}), 'failures', len(report['round_trip']['failures']))
    print(json.dumps(counterexamples, indent=0)[:1500])


if __name__ == '__main__':
    main()
