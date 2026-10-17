"""Development-only calibration and frozen known-problem reranker evaluation.

Absent cases remove the query's entire sibling family from a diagnostic index.
They measure controlled abstention, not naturally absent full-corpus coverage.
No generation, solution execution, hidden tests, or research-index mutations.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time

import numpy as np
from . import corpus, paraphrase, splits
from .lookup import LookupIndex, TOP_K, decide, load_thresholds
from .records import LANE_ROOT
from .rerank import DopplerReranker
from .run import recognition_query_text


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def bind_file(path, value):
    if path.exists():
        if json.loads(path.read_text()) != value:
            raise ValueError(f'Frozen artifact changed: {path}')
    else:
        path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def partition_queries(manifest):
    dev, evaluation = manifest['recognition_dev'], manifest['recognition']
    for field in ('qid', 'group'):
        if {q[field] for q in dev} & {q[field] for q in evaluation}:
            raise ValueError(f'Development/evaluation overlap: {field}')
    dev_targets = {q.get('target') or q.get('problem_uid') for q in dev}
    eval_targets = {q.get('target') or q.get('problem_uid') for q in evaluation}
    if dev_targets & eval_targets:
        raise ValueError('Development/evaluation target overlap')
    for rows in (dev, evaluation):
        if len({q['qid'] for q in rows}) != len(rows):
            raise ValueError('Duplicate query identity')
    return dev, evaluation


def diagnostic_entries(entries, query, problems):
    if query['kind'] != 'absent_exact':
        return list(range(len(entries)))
    problem = problems[query['problem_uid']]
    if not problem.slug:
        raise ValueError('Absent diagnostic requires an explicit canonical slug')
    family = splits.sibling_base(problem.slug)
    return [i for i, entry in enumerate(entries)
            if splits.sibling_base(entry.slug) != family and problem.uid not in entry.members]


def rerank_candidates(candidates, scores):
    if len(scores) != len(candidates) or not candidates:
        raise ValueError('Incomplete reranking')
    if any(type(s) not in (float, int) or not math.isfinite(s) for s in scores):
        raise ValueError('Invalid reranker score')
    return sorted([dict(c, score=float(s)) for c, s in zip(candidates, scores)],
                  key=lambda c: (-c['score'], c['key']))


def calibrate(rows, expected_queries):
    expected = {q['qid']: q for q in expected_queries}
    if len(rows) != len(expected) or {r['qid'] for r in rows} != set(expected):
        raise ValueError('Calibration requires every development query exactly once')
    if any(r['target'] != expected[r['qid']]['target'] for r in rows):
        raise ValueError('Calibration target mismatch')
    # Use actual score boundaries: rounding can skip the only safe threshold.
    scores = {r['reranked'][0]['score'] for r in rows}
    margins = {0.0} | {r['reranked'][0]['score'] - r['reranked'][1]['score'] for r in rows}
    scores.add(math.nextafter(max(scores), math.inf))
    best = None
    for score in sorted(scores):
        for margin in sorted(margins):
            thresholds = {'min_score': score, 'min_margin': margin}
            matched = [(decide(r['reranked'], thresholds).key, r['target']) for r in rows]
            wrong = sum(key is not None and key != target for key, target in matched)
            correct = sum(key is not None and key == target for key, target in matched)
            choice = (-wrong, correct, -score, -margin)
            if best is None or choice > best[0]:
                best = choice, thresholds, correct, wrong
    return dict(best[1], dev_correct=best[2], dev_wrong=best[3], dev_cases=len(rows))


def summarize(rows, thresholds, baseline):
    summary = {}
    for route, field, gates in [('baseline', 'retrieved', baseline), ('reranked', 'reranked', thresholds)]:
        groups = defaultdict(Counter)
        times = []
        for row in rows:
            key = decide(row[field], gates).key
            kind = 'controlled_absent' if row['kind'] == 'absent_exact' else row['kind']
            counts = groups[kind]
            counts['queries'] += 1
            counts['correct_abstention' if key is None and row['target'] is None else
                   'abstention' if key is None else 'correct_match' if key == row['target'] else 'wrong_match'] += 1
            if key is not None:
                counts['returned_independently_validated'] += int(key in row['validated_keys'])
            times.append(row['retrieval_seconds'] + (row['rerank_seconds'] if route == 'reranked' else 0))
        summary[route] = {'by_kind': dict(groups), 'p50_seconds': float(np.percentile(times, 50)),
                          'p95_seconds': float(np.percentile(times, 95))}
    return summary


def load_rows(path, queries):
    rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    expected = {q['qid']: q for q in queries}
    if len({r['qid'] for r in rows}) != len(rows) or any(
            r['qid'] not in expected or r['target'] != expected[r['qid']]['target']
            or r['kind'] != expected[r['qid']]['kind'] for r in rows):
        raise ValueError('Invalid resumed query rows')
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('dev', 'evaluate'))
    parser.add_argument('--name', required=True)
    parser.add_argument('--cli', type=Path, required=True)
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--limit', type=int, help='Bound new queries; incomplete development cannot freeze thresholds')
    args = parser.parse_args()
    if not args.name.replace('-', '').replace('_', '').isalnum() or args.limit is not None and args.limit <= 0:
        raise ValueError('Invalid run name or limit')
    entries = corpus.read_entries()
    if json.loads(corpus.KEYS_PATH.read_text()) != [e.key for e in entries]:
        raise ValueError('Corpus embedding order differs')
    vectors = np.load(corpus.EMBEDDINGS_PATH)
    manifest = splits.load_manifest()
    dev, evaluation = partition_queries(manifest)
    problems = splits.load_all()
    paragraphs = {r['key']: r for r in map(json.loads, paraphrase.PARAPHRASES_PATH.read_text().splitlines())}
    by_key = {e.key: e for e in entries}
    reranker = DopplerReranker(args.cli, args.model_dir)
    runtime_root = args.cli.resolve().parents[2]
    runtime_revision = subprocess.check_output(['git', '-C', str(runtime_root), 'rev-parse', 'HEAD'], text=True).strip()
    if subprocess.check_output(['git', '-C', str(runtime_root), 'status', '--porcelain', '--untracked-files=no'], text=True).strip():
        raise ValueError('Doppler tracked runtime changes must be committed before calibration')
    files = [corpus.ENTRIES_PATH, corpus.EMBEDDINGS_PATH, corpus.KEYS_PATH,
             LANE_ROOT/'contracts/sample_manifest.json', paraphrase.PARAPHRASES_PATH,
             Path(__file__), LANE_ROOT/'algsolve/rerank.py', LANE_ROOT/'algsolve/lookup.py',
             LANE_ROOT/'algsolve/embed.py']
    binding = {'files': {str(p.relative_to(LANE_ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
               'model_manifest_sha256': reranker.manifest_sha256, 'model_id': reranker.model_id,
               'runtime_revision': runtime_revision, 'top_k': TOP_K, 'dev_queries': dev, 'evaluation_queries': evaluation,
               'query_inputs': {q['qid']: {'text_sha256': hashlib.sha256(recognition_query_text(q, by_key, problems, paragraphs).encode()).hexdigest(),
                                           'active_indices_sha256': digest(diagnostic_entries(entries, q, problems))}
                                for q in dev + evaluation},
               'baseline_thresholds': load_thresholds(), 'embedding_device': 'cpu',
               'absent_policy': 'exclude canonical sibling family per absent query; controlled diagnostic',
               'latency_scope': 'warm embedding; fresh Doppler process including model loading per query'}
    directory = LANE_ROOT/'runs'/args.name
    directory.mkdir(parents=True, exist_ok=True)
    bind_file(directory/'contract.json', binding)
    calibration_path = directory/'calibration.json'
    if args.stage == 'evaluate':
        calibration = json.loads(calibration_path.read_text())
        dev_rows = load_rows(directory/'dev.jsonl', dev)
        if calibration['binding'] != digest(binding) or calibration['dev_rows_sha256'] != digest(dev_rows):
            raise ValueError('Calibration does not match frozen inputs/development rows')
        if calibration['thresholds'] != calibrate(dev_rows, dev):
            raise ValueError('Calibration thresholds differ from development fit')
    queries = dev if args.stage == 'dev' else evaluation
    rows_path = directory/f'{args.stage}.jsonl'
    rows = load_rows(rows_path, queries)
    if args.stage == 'dev' and calibration_path.exists():
        bind_file(calibration_path, {'binding': digest(binding), 'dev_rows_sha256': digest(rows),
                                    'thresholds': calibrate(rows, dev)})
        print('Development calibration already frozen; no new scoring.')
        return
    print(f'[run-contract] run_name={args.name} stage={args.stage} inputs_sha256={digest(binding)} '
          'decode=none device=cpu+webgpu runtime_mode=doppler-node schedule=serial '
          'hidden_tests=none generator=none', flush=True)
    from .embed import Embedder
    import torch
    torch.set_num_threads(4)
    embedder = Embedder(device='cpu')
    done = {r['qid'] for r in rows}
    new = 0
    with rows_path.open('a') as output:
        for query in queries:
            if query['qid'] in done:
                continue
            if args.limit is not None and new >= args.limit:
                break
            text = recognition_query_text(query, by_key, problems, paragraphs)
            indices = diagnostic_entries(entries, query, problems)
            active = [entries[i] for i in indices]
            lookup = LookupIndex(active, vectors[indices])
            started = time.perf_counter()
            vector = embedder.encode([text], query=True)[0]
            candidates = lookup.scored_candidates(text, vector)
            retrieved_at = time.perf_counter()
            try:
                ranked = rerank_candidates(candidates, reranker(text, [by_key[c['key']].query_text() for c in candidates]))
            except Exception as error:
                failure = {'binding': digest(binding), 'stage': args.stage, 'qid': query['qid'],
                           'completed_queries': len(rows), 'error_type': type(error).__name__,
                           'message': str(error), 'query_sha256': hashlib.sha256(text.encode()).hexdigest(),
                           'candidate_keys': [c['key'] for c in candidates]}
                for field in ('stdout', 'stderr'):
                    value = getattr(error, field, '') or ''
                    failure[field] = value.decode(errors='replace') if isinstance(value, bytes) else value
                # Keep every failure receipt. It never becomes a scored row or
                # an abstention, and a later retry does not erase the evidence.
                (directory/f'failure-{query["qid"]}-{time.time_ns()}.json').write_text(
                    json.dumps(failure, indent=2) + '\n')
                raise
            row = {**query, 'retrieved': candidates, 'reranked': ranked,
                   'retrieval_seconds': retrieved_at - started, 'rerank_seconds': time.perf_counter() - retrieved_at,
                   'query_sha256': hashlib.sha256(text.encode()).hexdigest(),
                   'index_entries': len(active), 'excluded_entries': len(entries) - len(active),
                   'validated_keys': [c['key'] for c in candidates if any(r.get('validated') for r in by_key[c['key']].references)]}
            rows.append(row)
            output.write(json.dumps(row, allow_nan=False) + '\n'); output.flush()
            new += 1
            print(f'[{args.stage}] {len(rows)}/{len(queries)} rerank_seconds={row["rerank_seconds"]:.3f}', flush=True)
    if len(rows) != len(queries):
        print(f'Partial: {len(rows)}/{len(queries)}; no calibration or final summary emitted.')
        return
    if args.stage == 'dev':
        calibration = {'binding': digest(binding), 'dev_rows_sha256': digest(rows), 'thresholds': calibrate(rows, dev)}
        bind_file(calibration_path, calibration)
    result = {'binding': digest(binding), 'stage': args.stage, 'completed': len(rows),
              'comparison': summarize(rows, calibration['thresholds'], binding['baseline_thresholds']),
              'limits': ['Recognition decisions, not newly judged answers.',
                         'Model-generated paraphrases retain starter signatures.',
                         'Absent cases use controlled family exclusion, not natural full-corpus absence.',
                         'Stored independent validation is provenance, not query correctness.']}
    bind_file(directory/f'{args.stage}-summary.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
