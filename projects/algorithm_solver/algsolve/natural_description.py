"""Development-only natural-description recognition diagnostic; no code execution.

Run the unchanged whole-corpus lookup on query text alone. Scorer labels, desired
clarifications, corpus signatures and public/hidden tests never enter the query.
This does not fit thresholds, generate code or consume protected composition data.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import re
import time

from .records import LANE_ROOT

DEFAULT_DATASET = LANE_ROOT / 'contracts/natural_description_dev_v1.json'


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1 << 22), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load_dataset(path: Path) -> dict:
    data = json.loads(path.read_text())
    if data.get('schema_version') != 1 or data.get('partition') != 'development':
        raise ValueError('Only schema-v1 development descriptions are admitted')
    if not data.get('authorship') or not data.get('review_status') or not data.get('limits'):
        raise ValueError('Authorship, review status and evidence limits are required')
    cases = data.get('cases')
    if not isinstance(cases, list) or not cases:
        raise ValueError('A nonempty case list is required')
    seen = set()
    for row in cases:
        if not isinstance(row.get('id'), str) or not row['id'] or row['id'] in seen:
            raise ValueError('Case identities must be unique nonempty strings')
        seen.add(row['id'])
        if any(not isinstance(row.get(k), str) or not row[k].strip() for k in ('query', 'family', 'kind')):
            raise ValueError('Every case needs query text, family and kind')
        expected = row.get('expected', {})
        action, keys = expected.get('action'), expected.get('keys')
        if action not in ('match', 'clarify', 'abstain') or not isinstance(keys, list):
            raise ValueError('Invalid expected action or keys')
        if any(not isinstance(k, str) or not k.startswith('lc:') for k in keys) or len(keys) != len(set(keys)):
            raise ValueError('Invalid or duplicate target keys')
        if bool(keys) != (action == 'match'):
            raise ValueError('Only match cases must name one or more equivalent keys')
        if action == 'clarify' and (not expected.get('missing_requirements') or not expected.get('question')):
            raise ValueError('Clarification cases must identify missing requirements and a question')
    return data


def score(expected: dict, prediction: dict) -> dict:
    """Identity/action scoring only. Never infer correctness from retrieved tests."""
    action = prediction['decision']
    if action not in ('match', 'abstain', 'clarify'):
        raise ValueError('Unknown prediction decision')
    matched = prediction.get('key')
    if (action == 'match') != (isinstance(matched, str) and bool(matched)):
        raise ValueError('Only match predictions may contain an accepted identity')
    keys = expected['keys']
    correct_match = action == 'match' and matched in keys
    correct_action = correct_match if expected['action'] == 'match' else action == expected['action']
    candidates = prediction.get('candidates', [])
    return {
        'decision_correct': correct_action,
        'correct_match': correct_match,
        'wrong_match': action == 'match' and not correct_match,
        'abstained': action == 'abstain',
        'clarification_requested': action == 'clarify',
        'clarification_needed': expected['action'] == 'clarify',
        'top1_identity_correct': bool(keys and candidates and candidates[0]['key'] in keys),
        'top5_contains_identity': bool(keys and any(c['key'] in keys for c in candidates[:5])),
    }


def evaluate_case(case: dict, recognize) -> dict:
    started = time.perf_counter()
    # This is the full inference boundary: no labels, signatures or examples.
    prediction = recognize(case['query'])
    seconds = time.perf_counter() - started
    return {'id': case['id'], 'family': case['family'], 'kind': case['kind'],
            'expected': case['expected'], 'prediction': prediction,
            'seconds': seconds, **score(case['expected'], prediction)}


def percentile(values: list[float], fraction: float) -> float:
    values = sorted(values)
    at = (len(values) - 1) * fraction
    lo, hi = math.floor(at), math.ceil(at)
    return values[lo] + (values[hi] - values[lo]) * (at - lo)


def summarize(rows: list[dict]) -> dict:
    def group(items):
        count = Counter()
        for row in items:
            count['queries'] += 1
            count['match_targets'] += row['expected']['action'] == 'match'
            for field in ('decision_correct', 'correct_match', 'wrong_match', 'abstained',
                          'clarification_needed', 'clarification_requested',
                          'top1_identity_correct', 'top5_contains_identity'):
                count[field] += row[field]
        latencies = [r['seconds'] for r in items]
        return {**dict(count), 'p50_seconds': percentile(latencies, .5),
                'p95_seconds': percentile(latencies, .95)}
    if not rows:
        raise ValueError('Cannot summarize an empty run')
    groups = defaultdict(list)
    for row in rows:
        groups[row['kind']].append(row)
    return {'overall': group(rows), 'by_kind': {k: group(v) for k, v in groups.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.name):
        parser.error('Run name must contain only letters, numbers, underscore and hyphen')
    data = load_dataset(args.dataset)
    directory = LANE_ROOT / 'runs' / args.name
    if directory.exists():
        raise ValueError('Run already exists; use a fresh name')
    import numpy as np
    import torch
    from . import corpus
    from .embed import Embedder, EXPECTED_SHA256
    from .lookup import LookupIndex, load_thresholds, THRESHOLDS_PATH

    torch.set_num_threads(4)
    print(f'[run-contract] run_name={args.name} pairs_input_spec={args.dataset} resume_from=none '
          f'resume_stage=none decode=none eval_dataset_paths={args.dataset} device={args.device} '
          f'schedule=serial runtime_mode={args.device} sweep_mode=after_train', flush=True)
    print(f'cuda_available={torch.cuda.is_available()} device_count={torch.cuda.device_count()} '
          f'target_device={args.device}', flush=True)
    probe = torch.ones((2, 2), device=args.device)
    if not torch.equal((probe @ probe).cpu(), torch.full((2, 2), 2.)):
        raise RuntimeError('Device compute probe failed')
    entries = corpus.read_entries()
    keys = [entry.key for entry in entries]
    if not keys or len(keys) != len(set(keys)) or json.loads(corpus.KEYS_PATH.read_text()) != keys:
        raise ValueError('Corpus identity/order mismatch')
    missing = {k for row in data['cases'] for k in row['expected']['keys']} - set(keys)
    if missing:
        raise ValueError(f'Annotated targets absent from corpus: {sorted(missing)}')
    vectors = np.load(corpus.EMBEDDINGS_PATH)
    if vectors.ndim != 2 or len(vectors) != len(keys) or not np.isfinite(vectors).all():
        raise ValueError('Invalid corpus vectors')
    thresholds = load_thresholds()
    index = LookupIndex(entries, vectors)
    contract = {
        'schema_version': 1, 'partition': 'development', 'cases': len(data['cases']),
        'dataset_sha256': sha(args.dataset), 'authorship': data['authorship'],
        'review_status': data['review_status'], 'index_entries': len(keys),
        'index_sha256': {p.name: sha(p) for p in (corpus.ENTRIES_PATH, corpus.KEYS_PATH, corpus.EMBEDDINGS_PATH)},
        'source_sha256': {name: sha(LANE_ROOT / 'algsolve' / name) for name in
                          ('natural_description.py', 'lookup.py', 'embed.py', 'corpus.py', 'splits.py', 'records.py')},
        'thresholds': thresholds, 'thresholds_sha256': sha(THRESHOLDS_PATH),
        'embedding_weights': EXPECTED_SHA256, 'device': args.device,
        'dtype': 'float32' if args.device == 'cpu' else 'float16',
        'torch': torch.__version__, 'numpy': np.__version__,
        'device_name': torch.cuda.get_device_name() if args.device == 'cuda' else 'CPU',
        'generation': False, 'reranking': False, 'threshold_fitting': False,
        'query_input': 'authored description only; no inferred or corpus-derived signature/examples',
        'clarification_policy': 'unchanged baseline has no clarification action; abstention does not satisfy it',
        'limits': data['limits'],
    }
    directory.mkdir(parents=True, exist_ok=False)
    (directory / 'contract.json').write_text(json.dumps(contract, indent=2) + '\n')
    started = time.perf_counter()
    embedder = Embedder(device=args.device)
    load_seconds = time.perf_counter() - started

    def recognize(query):
        vector = embedder.encode([query], query=True)[0]
        return asdict(index.match(query, vector, thresholds))

    rows = []
    with (directory / 'recognition.jsonl').open('x') as stream:
        for case in data['cases']:
            row = evaluate_case(case, recognize)
            stream.write(json.dumps(row, allow_nan=False) + '\n')
            stream.flush()
            rows.append(row)
            print(f'[description] {len(rows)}/{len(data["cases"])} {row["id"]} '
                  f'{row["prediction"]["decision"]} {row["prediction"]["key"]}', flush=True)
    summary = {
        'complete': len(rows) == len(data['cases']), 'contract_sha256': sha(directory / 'contract.json'),
        'rows_sha256': sha(directory / 'recognition.jsonl'), 'embedding_load_seconds': load_seconds,
        **summarize(rows), 'limits': contract['limits'],
        'latency_scope': 'serial warm embedding plus lookup/decision; cold model loading separate; no program checks',
    }
    (directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
