"""Frozen public-text ranking experiment. Never an answer/recognition endpoint."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import resource
import time

from projects.algorithm_solver.catalogue.cpu_encoder import PinnedCPUEncoder
from projects.algorithm_solver.catalogue.known_spec_service import KnownSpecService


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pinned(path, expected):
    if sha(path) != expected:
        raise ValueError('freeze hash mismatch')
    return json.loads(Path(path).read_text())


def rank(scores, ids):
    if len(scores) != len(ids) or not all(math.isfinite(float(s)) for s in scores):
        raise ValueError('invalid scores')
    # Deterministic identity tie order only, never implementation availability.
    return sorted(zip(ids, map(float, scores)), key=lambda x: (-x[1], x[0]))


def outcome(query, ranked, service, *, truncated):
    result = {'query_id': query['query_id'], 'kind': query['kind'],
              'status': 'abstain', 'reason': 'truncation' if truncated else 'semantic_identity_not_proven',
              'accepted_answer': None, 'clarification_questions': [],
              'unknown_interpretation_retained': True, 'outside_pilot_interpretation_retained': True,
              'ranking_is_semantic_proof': False, 'rankings': [], 'candidate_artifact_metadata': []}
    if truncated:
        return result
    result['rankings'] = [{'problem_id': ident, 'cosine': score} for ident, score in ranked]
    # Metadata is subordinate evidence only, not an approval of the query identity.
    result['candidate_artifact_metadata'] = [service.request(ident, include_source=False) for ident, _ in ranked[:3]]
    if query['kind'] == 'positive':
        result['expected_rank'] = next(i for i, (ident, _) in enumerate(ranked, 1) if ident in query['expected_ids'])
    return result


def run(args):
    base = Path(__file__).parent
    freeze = pinned(base / 'freeze.json', args.freeze_sha256)
    index = pinned(base / 'index.json', freeze['index_sha256'])['documents']
    queries = pinned(base / 'queries.json', freeze['queries_sha256'])['queries']
    if sha(__file__) != freeze['runner_sha256']:
        raise ValueError('runner changed since freeze')
    if len(index) != 20 or len(queries) != 28 or len({r['problem_id'] for r in index}) != 20:
        raise ValueError('population changed')
    service = KnownSpecService.from_config(args.service_config, freeze['known_spec_config_sha256'])
    for row in index:
        if sha(base.parent / row['contract_path']) != row['contract_sha256']:
            raise ValueError('public contract changed')
        value = service.request(row['problem_id'], include_source=False)
        if value['status'] != 'matched':
            raise ValueError('pilot identity unavailable in frozen catalogue')
    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (120, 125))
    encoder = PinnedCPUEncoder(args.model_root,
        encoder_manifest=base.parent / 'ENCODER-PROVISIONING-PROPOSAL-v1.json',
        encoder_manifest_sha256=freeze['encoder_manifest_sha256'],
        cpu_manifest=base.parent / 'CPU-ENVIRONMENT-PROPOSAL-v1.json',
        cpu_manifest_sha256=freeze['cpu_manifest_sha256'],
        native_python_sha256=freeze['native_python_sha256'], threads=2, batch_size=2)
    if sha(base.parent / 'cpu_encoder.py') != freeze['encoder_adapter_sha256']:
        raise ValueError('encoder adapter changed')
    start = time.monotonic()
    docs = encoder.encode([d['text'] for d in index]); document_info = encoder.last_request_info
    first = time.monotonic()
    vectors = encoder.encode([q['text'] for q in queries], query=True); query_info = encoder.last_request_info
    scores = vectors @ docs.T
    ids = [d['problem_id'] for d in index]
    rows = [outcome(q, rank(s, ids), service,
                    truncated=any(document_info['truncated']) or query_info['truncated'][i])
            for i, (q, s) in enumerate(zip(queries, scores))]
    positives = [r for r in rows if r['kind'] == 'positive']
    ranks = [r.get('expected_rank') for r in positives]
    report = {'schema': 'gamma.description-ranking-diagnostic.v1', 'freeze_sha256': args.freeze_sha256,
        'encoder_identity': encoder.identity(), 'scope': freeze['scope'], 'results': rows,
        'document_request_metadata': document_info, 'query_request_metadata': query_info,
        'empirical_rank_metrics': {'positive_denominator': 20, 'ranked_positive_count': sum(x is not None for x in ranks),
          'top1_hits': sum(x == 1 for x in ranks), 'top3_hits': sum(x is not None and x <= 3 for x in ranks),
          'reciprocal_rank_sum': sum(1/x for x in ranks if x is not None)},
        'serving_metrics': {'accepted_answers': 0, 'abstentions': len(rows), 'semantic_precision_estimated': False},
        'first_document_encode_seconds': first-start, 'total_seconds': time.monotonic()-start,
        'timing_caveat': 'First call includes verification/loading; OS cache uncontrolled. Not cold-cache or production latency.',
        'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'old_calibration_reused': False, 'threshold_tuning': False, 'candidate_source_reads': 0,
        'case_reads': 0, 'protected_data_reads': 0, 'recognition_release_qualified': False}
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('freeze-sha256', 'service-config', 'model-root', 'output'):
        p.add_argument('--'+name, required=True)
    run(p.parse_args())
