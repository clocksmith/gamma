"""Known-query recognition diagnostic against the separate whole-corpus index.

Uses existing paraphrases only; never generates queries or refits thresholds.
Old absent-query labels do not apply to this larger index, so they are excluded.
This is recognition, not held-out solving or evidence for composition.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
import time

import numpy as np
from . import corpus, paraphrase, splits
from .lookup import LookupIndex, load_thresholds
from .records import LANE_ROOT
from .run import recognition_query_text
from .rerank_recognition import diagnostic_entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    parser.add_argument('--partition', choices=('development', 'evaluation'), default='evaluation')
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    args = parser.parse_args()
    if not args.name.replace('-', '').replace('_', '').isalnum():
        raise ValueError('Invalid run name')
    print(f'[run-contract] run_name={args.name} pairs_input_spec=existing-recognition-known-queries '
          'resume_from=bound-records resume_stage=recognition decode=none eval_dataset_paths=recognition '
          f'device={args.device} schedule=serial runtime_mode={args.device} sweep_mode=after_train', flush=True)
    import torch
    from .embed import Embedder
    torch.set_num_threads(4)
    probe = torch.ones((2, 2), device=args.device) @ torch.ones((2, 2), device=args.device)
    if not torch.equal(probe.cpu(), torch.full((2, 2), 2.)):
        raise RuntimeError('Embedding device compute probe failed')
    entries = corpus.read_entries()
    if json.loads(corpus.KEYS_PATH.read_text()) != [e.key for e in entries]:
        raise ValueError('Corpus embedding key order differs')
    vectors = np.load(corpus.EMBEDDINGS_PATH)
    index = LookupIndex(entries, vectors)
    by_key = {e.key:e for e in entries}
    manifest = splits.load_manifest()
    paragraphs = {row['key']:row for row in map(json.loads, paraphrase.PARAPHRASES_PATH.read_text().splitlines()) if row}
    problems = splits.load_all()
    queries = (manifest['recognition_dev'] if args.partition == 'development' else
               [q for q in manifest['recognition'] if q['kind'] != 'absent_exact'])
    thresholds = load_thresholds()
    binding = hashlib.sha256()
    for path in [corpus.ENTRIES_PATH, corpus.KEYS_PATH, corpus.EMBEDDINGS_PATH, LANE_ROOT/'contracts/sample_manifest.json',
                 paraphrase.PARAPHRASES_PATH, LANE_ROOT/'algsolve/corpus_recognition.py',
                 LANE_ROOT/'algsolve/embed.py', LANE_ROOT/'algsolve/lookup.py']:
        binding.update(path.read_bytes())
    binding.update(json.dumps(thresholds, sort_keys=True).encode())
    contract = {'inputs_sha256':binding.hexdigest(), 'queries':len(queries), 'index_entries':len(entries),
                'partition': args.partition, 'embedding_device': args.device,
                'embedding_dtype':'float32' if args.device == 'cpu' else 'float16', 'thresholds':thresholds,
                'torch_version': torch.__version__, 'hsa_override': os.environ.get('HSA_OVERRIDE_GFX_VERSION'),
                'gpu_name': torch.cuda.get_device_name() if args.device == 'cuda' else None,
                'absent_policy': 'development only: exclude entire canonical sibling family per absent query',
                'label':'prior model exposure unknown; known-problem recognition only'}
    directory = LANE_ROOT/'runs'/args.name
    directory.mkdir(parents=True, exist_ok=True)
    contract_path = directory/'contract.json'
    if contract_path.exists() and json.loads(contract_path.read_text()) != contract:
        raise ValueError('Resume inputs changed')
    contract_path.write_text(json.dumps(contract,indent=2)+'\n')
    rows_path = directory/'recognition.jsonl'
    rows = [json.loads(line) for line in rows_path.read_text().splitlines()] if rows_path.exists() else []
    if len({r['i'] for r in rows}) != len(rows) or any(
            type(r['i']) is not int or not 0 <= r['i'] < len(queries)
            or r['target'] != queries[r['i']]['target'] or r['kind'] != queries[r['i']]['kind'] for r in rows):
        raise ValueError('Invalid resumed recognition rows')
    done = {r['i'] for r in rows}
    started = time.perf_counter()
    embedder = Embedder(device=args.device)
    load_seconds = time.perf_counter()-started
    with rows_path.open('a') as out:
        for i,q in enumerate(queries):
            if i in done: continue
            text = recognition_query_text(q,by_key,problems,paragraphs)
            indices = diagnostic_entries(entries, q, problems)
            active_index = LookupIndex([entries[j] for j in indices], vectors[indices]) if q['kind'] == 'absent_exact' else index
            started = time.perf_counter()
            vector = embedder.encode([text],query=True)[0]
            match = active_index.match(text,vector,thresholds)
            row = {'i':i, 'kind':q['kind'], 'target':q['target'], 'matched':match.key,
                   'decision':match.decision, 'correct':match.key == q['target'],
                   'seconds':time.perf_counter()-started, 'candidates':match.candidates,
                   'numbers_preserved': paragraphs.get(q['target'],{}).get('numbers_preserved') if q['kind'] != 'exact' else None}
            rows.append(row); out.write(json.dumps(row)+'\n'); out.flush()
            print(f'[recognition] {len(rows)}/{len(queries)}', flush=True)
    by_kind = defaultdict(Counter)
    for row in rows:
        by_kind[row['kind']]['queries'] += 1
        by_kind[row['kind']]['correct' if row['correct'] else 'abstain' if row['decision']=='abstain' else 'wrong_match'] += 1
    summary = {**contract,'completed':len(rows),'by_kind':dict(by_kind),
               'embedding_load_seconds': load_seconds,
               'p50_seconds': float(np.percentile([r['seconds'] for r in rows], 50)),
               'p95_seconds': float(np.percentile([r['seconds'] for r in rows], 95)),
               'failures':[r for r in rows if not r['correct']],
               'limitation':'Existing model-generated paraphrases with unchanged starter code; no human paraphrase validation or unseen-problem claim.'}
    (directory/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'completed':len(rows),'by_kind':dict(by_kind)},indent=2))

if __name__ == '__main__': main()
