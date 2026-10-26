"""Paired raw-yes versus yes-minus-no diagnostics from identical inference.

Only explicit development inputs or the existing synthetic integration probes
are accepted. No catalogue, protected cohort, source code or training is opened.
Calibration on these inputs is development evidence, never held-out accuracy.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import time

from .doppler_runtime import DopplerRuntime, sha
from .lookup import decide
from .rerank_recognition import calibrate

POLICIES = ('true_logit', 'logit_difference')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def validate_cohort(cohort):
    if (cohort.get('schema') != 'gamma.rerank-policy-input.v1'
            or cohort.get('partition') != 'development'):
        raise ValueError('explicit development cohort required')
    cases = cohort.get('cases')
    if type(cases) is not list or not 1 <= len(cases) <= 100:
        raise ValueError('expected 1–100 development queries')
    ids = set()
    for case in cases:
        ident = case.get('id')
        if type(ident) is not str or not ident or ident in ids:
            raise ValueError('unique nonempty query IDs required')
        ids.add(ident)
        if type(case.get('query')) is not str or not case['query'].strip():
            raise ValueError('nonempty query required')
        documents = case.get('documents')
        if type(documents) is not list or not 2 <= len(documents) <= 50:
            raise ValueError('each query requires 2–50 fixed candidates')
        keys = set()
        for doc in documents:
            if type(doc.get('key')) is not str or not doc['key'] or doc['key'] in keys:
                raise ValueError('unique nonempty candidate keys required')
            keys.add(doc['key'])
            if type(doc.get('text')) is not str or not doc['text'].strip():
                raise ValueError('nonempty candidate document required')
        # An absent positive stays in the denominator: reranking cannot recover it.
        if 'target' not in case or (case['target'] is not None
                and (type(case['target']) is not str or not case['target'])):
            raise ValueError('explicit target identity or null control required')
        if len(json.dumps(case).encode()) > 500_000:
            raise ValueError('query and candidates exceed bounded packet size')
    return cases


def validate_review(cohort, review):
    if (review.get('schema') != 'gamma.rerank-confusion-review.v1'
            or review.get('approved') is not True
            or review.get('cohort_sha256') != digest(cohort)
            or review.get('blockers') != []):
        raise ValueError('approved independent review must bind this exact cohort without blockers')


def rank_logits(case, evidence, policy):
    if policy not in POLICIES:
        raise ValueError('unknown scoring policy')
    if len(evidence) != len(case['documents']):
        raise ValueError('incomplete candidate evidence')
    result = []
    for doc, row in zip(case['documents'], evidence):
        if row.get('key') != doc['key'] or row.get('document') != doc['text'].strip():
            raise ValueError('candidate evidence identity/order mismatch')
        yes, no = row.get('trueLogit'), row.get('falseLogit')
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in (yes, no)):
            raise ValueError('finite yes/no logits required')
        score = yes if policy == 'true_logit' else yes - no
        if not math.isfinite(score):
            raise ValueError('nonfinite derived score')
        result.append({'key': doc['key'], 'score': score})
    return sorted(result, key=lambda row: (-row['score'], row['key']))


def summarize(cohort, observations):
    cases = validate_cohort(cohort)
    if [row['id'] for row in observations] != [case['id'] for case in cases]:
        raise ValueError('every frozen query required exactly once in original order')
    if any(row.get('case_sha256') != digest(case) for case, row in zip(cases, observations)):
        raise ValueError('observation differs from frozen query/candidates/target')
    positives = sum(case['target'] is not None for case in cases)
    present = sum(case['target'] in {d['key'] for d in case['documents']} for case in cases)
    expected = [{'qid': c['id'], 'target': c['target']} for c in cases]
    result = {'queries': len(cases), 'positive_queries': positives,
              'control_queries': len(cases) - positives,
              'positive_targets_in_candidates': present,
              'candidate_recall': present / positives if positives else None,
              'policies': {}, 'recognition_qualified': False,
              'scope': 'Same-inference development comparison; independent per-policy development calibration. '
                       'No held-out accuracy, catalogue coverage, deployment or training claim.'}
    tops = {}
    for policy in POLICIES:
        rows = [dict(qid=case['id'], target=case['target'],
                     reranked=rank_logits(case, obs['evidence'], policy))
                for case, obs in zip(cases, observations)]
        thresholds = calibrate(rows, expected)
        decisions = [decide(row['reranked'], thresholds).key for row in rows]
        correct = sum(key is not None and key == case['target'] for key, case in zip(decisions, cases))
        wrong = sum(key is not None and key != case['target'] for key, case in zip(decisions, cases))
        top_correct = sum(row['target'] is not None and row['reranked'][0]['key'] == row['target'] for row in rows)
        tops[policy] = [row['reranked'][0]['key'] for row in rows]
        result['policies'][policy] = {
            'thresholds': thresholds, 'top1_correct': top_correct,
            'top1_accuracy_positive': top_correct / positives if positives else None,
            'top1_accuracy_when_present': top_correct / present if present else None,
            'correct_accepted': correct, 'wrong_accepted': wrong,
            'abstentions': len(cases) - correct - wrong,
            'development_precision': correct / (correct + wrong) if correct + wrong else None,
            'development_recall': correct / positives if positives else None,
        }
    result['top1_disagreements'] = sum(a != b for a, b in zip(*tops.values()))
    return result


def collect(runtime, case):
    evidence, receipts = [], []
    started = time.monotonic()
    documents = case['documents']
    for start in range(0, len(documents), 10):
        chunk = documents[start:start + 10]
        rows = runtime.rerank_evidence(case['query'], [d['text'] for d in chunk])
        if len(rows) != len(chunk):
            raise ValueError('missing chunk evidence')
        evidence.extend(dict(row, key=doc['key'], index=start + i)
                        for i, (doc, row) in enumerate(zip(chunk, rows)))
        receipts.append(copy.deepcopy(runtime.last_receipt))
    # Validate both views before retaining a completed observation.
    for policy in POLICIES:
        rank_logits(case, evidence, policy)
    return {'id': case['id'], 'case_sha256': digest(case), 'evidence': evidence,
            'receipts': receipts, 'inference_seconds': time.monotonic() - started}


def synthetic_cohort():
    from .doppler_probe import CASES
    return {'schema': 'gamma.rerank-policy-input.v1', 'partition': 'development',
            'scope': 'Three existing synthetic integration probes; not representative recognition data.',
            'cases': [{'id': ident, 'query': query, 'target': 'relevant',
                       'documents': [{'key': key, 'text': text} for key, text in
                                     zip(('relevant', 'irrelevant'), documents)]}
                      for ident, query, documents in CASES]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--cohort', type=Path, help='Explicit permitted development text; never reserved data')
    source.add_argument('--synthetic', action='store_true')
    parser.add_argument('--review', type=Path, help='Independent approval bound to the exact custom cohort')
    for name in ('doppler-root', 'embedding-model', 'reranker-model', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--surface', choices=('node', 'browser'), default='node')
    parser.add_argument('--runtime-config', type=Path)
    args = parser.parse_args()
    if args.cohort and args.cohort.stat().st_size > 4 * 1024**2:
        parser.error('development input exceeds 4 MiB')
    cohort = json.loads(args.cohort.read_text()) if args.cohort else synthetic_cohort()
    cases = validate_cohort(cohort)
    if args.cohort and args.review is None:
        parser.error('--cohort requires --review; preserve unreviewed drafts without model execution')
    review_binding = None
    if args.review:
        if args.review.stat().st_size > 1024**2:
            parser.error('review artifact exceeds 1 MiB')
        review_raw = args.review.read_bytes()
        review = json.loads(review_raw)
        validate_review(cohort, review)
        review_binding = {'sha256': hashlib.sha256(review_raw).hexdigest(), 'review': review}
    config = json.loads(args.runtime_config.read_text()) if args.runtime_config else {}
    args.output.mkdir(parents=True, exist_ok=False)
    with DopplerRuntime(args.doppler_root, args.embedding_model, args.reranker_model,
                        surface=args.surface, timeout=90, embedding_config=config.get('embedding'),
                        reranker_config=config.get('rerank')) as runtime:
        contract = {'schema': 'gamma.rerank-policy-comparison.v1', 'cohort': cohort,
                    'cohort_sha256': digest(cohort), 'runtime': runtime.identity,
                    'policies': POLICIES, 'chunk_size': 10,
                    'code_sha256': {name: sha(Path(__file__).with_name(name)) for name in
                        ('rerank_policy_comparison.py', 'doppler_runtime.py', 'rerank.py',
                         'lookup.py', 'rerank_recognition.py', 'doppler_probe.py')},
                    'calibration_partition': 'development', 'recognition_qualified': False}
        contract['independent_review'] = review_binding
        (args.output/'contract.json').write_text(json.dumps(contract, indent=2, allow_nan=False) + '\n')
        observations = []
        with (args.output/'observations.jsonl').open('x') as stream:
            for case in cases:
                row = collect(runtime, case)
                stream.write(json.dumps(row, allow_nan=False) + '\n'); stream.flush()
                observations.append(row)
                print(json.dumps({'completed': len(observations), 'total': len(cases)}), flush=True)
        result = summarize(cohort, observations)
        result['contract_sha256'] = sha(args.output/'contract.json')
        result['observations_sha256'] = sha(args.output/'observations.jsonl')
        (args.output/'summary.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
        print(json.dumps(result, allow_nan=False))


if __name__ == '__main__':
    main()
