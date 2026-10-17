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
import time

import numpy as np
from . import corpus, paraphrase, splits
from .lookup import LookupIndex, load_thresholds
from .records import LANE_ROOT
from .run import recognition_query_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    if not args.name.replace('-', '').replace('_', '').isalnum():
        raise ValueError('Invalid run name')
    print(f'[run-contract] run_name={args.name} pairs_input_spec=existing-recognition-known-queries '
          'resume_from=bound-records resume_stage=recognition decode=none eval_dataset_paths=recognition '
          'device=cpu schedule=serial runtime_mode=cpu sweep_mode=after_train', flush=True)
    import torch
    from .embed import Embedder
    torch.set_num_threads(4)
    entries = corpus.read_entries()
    if json.loads(corpus.KEYS_PATH.read_text()) != [e.key for e in entries]:
        raise ValueError('Corpus embedding key order differs')
    index = LookupIndex(entries, np.load(corpus.EMBEDDINGS_PATH))
    by_key = {e.key:e for e in entries}
    manifest = splits.load_manifest()
    paragraphs = {row['key']:row for row in map(json.loads, paraphrase.PARAPHRASES_PATH.read_text().splitlines()) if row}
    problems = splits.load_all()
    queries = [q for q in manifest['recognition'] if q['kind'] != 'absent_exact']
    thresholds = load_thresholds()
    binding = hashlib.sha256()
    for path in [corpus.ENTRIES_PATH, corpus.EMBEDDINGS_PATH, LANE_ROOT/'contracts/sample_manifest.json', paraphrase.PARAPHRASES_PATH]:
        binding.update(path.read_bytes())
    binding.update(json.dumps(thresholds, sort_keys=True).encode())
    contract = {'inputs_sha256':binding.hexdigest(), 'queries':len(queries), 'index_entries':len(entries),
                'embedding_device':'cpu', 'embedding_dtype':'float32', 'thresholds':thresholds,
                'label':'prior model exposure unknown; known-problem recognition only'}
    directory = LANE_ROOT/'runs'/args.name
    directory.mkdir(parents=True, exist_ok=True)
    contract_path = directory/'contract.json'
    if contract_path.exists() and json.loads(contract_path.read_text()) != contract:
        raise ValueError('Resume inputs changed')
    contract_path.write_text(json.dumps(contract,indent=2)+'\n')
    rows_path = directory/'recognition.jsonl'
    rows = [json.loads(line) for line in rows_path.read_text().splitlines()] if rows_path.exists() else []
    done = {r['i'] for r in rows}
    embedder = Embedder(device='cpu')
    with rows_path.open('a') as out:
        for i,q in enumerate(queries):
            if i in done: continue
            text = recognition_query_text(q,by_key,problems,paragraphs)
            started = time.perf_counter()
            vector = embedder.encode([text],query=True)[0]
            match = index.match(text,vector,thresholds)
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
               'failures':[r for r in rows if not r['correct']],
               'limitation':'Existing model-generated paraphrases with unchanged starter code; no human paraphrase validation or unseen-problem claim.'}
    (directory/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'completed':len(rows),'by_kind':dict(by_kind)},indent=2))

if __name__ == '__main__': main()
