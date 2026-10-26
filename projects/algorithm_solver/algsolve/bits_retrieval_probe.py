"""Dense recall over the existing index using only reviewed development queries."""
import json
from pathlib import Path
import time

from .bits_server import argument_parser, create_recognizer
from .doppler_runtime import sha
from .rerank_policy_comparison import validate_cohort, validate_review


def main():
    parser = argument_parser()
    parser.add_argument('--cohort', type=Path, required=True)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.cohort.stat().st_size > 4*1024**2 or args.review.stat().st_size > 1024**2:
        raise ValueError('development inputs exceed bound')
    cohort = json.loads(args.cohort.read_text())
    cases = validate_cohort(cohort)
    validate_review(cohort, json.loads(args.review.read_text()))
    args.output.mkdir(parents=True, exist_ok=False)
    recognizer = create_recognizer(args)
    contract = {'schema': 'gamma.bits-retrieval-probe.v1', 'recognition_qualified': False,
                'cohort_sha256': sha(args.cohort), 'review_sha256': sha(args.review),
                'index': recognizer.identity, 'indexed_count': len(recognizer.keys),
                'scope': 'Existing frozen vector population; reviewed consumed development queries. '
                         'No new source access, reranking, threshold calibration or confirmation.'}
    (args.output/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    rows = []
    try:
        for case in cases:
            start = time.perf_counter()
            vector = recognizer.runtime.encode([case['query']], query=True)[0]
            truncated = recognizer.runtime.last_receipt['embedding_rows'][0].get('truncated')
            retrieved = recognizer.retrieve(vector, 32) if not truncated else []
            canonical = [recognizer.metadata[row['key']]['problem_id'] for row in retrieved]
            rank = canonical.index(case['target'])+1 if case['target'] in canonical else None
            row = {'id': case['id'], 'target': case['target'], 'rank': rank,
                   'truncated': truncated, 'candidates': retrieved,
                   'reviewed_group_hits_at32': sum(doc['key'] in canonical for doc in case['documents']),
                   'reviewed_group_size': len(case['documents']),
                   'elapsed_ms': (time.perf_counter()-start)*1000}
            rows.append(row)
            with (args.output/'observations.jsonl').open('a') as stream:
                stream.write(json.dumps(row)+'\n')
        positives = [row for row in rows if row['target'] is not None]
        summary = {'schema': 'gamma.bits-retrieval-summary.v1', 'recognition_qualified': False,
                   'indexed_count': len(recognizer.keys), 'queries': len(rows), 'positives': len(positives),
                   'hits': {str(k): sum(row['rank'] is not None and row['rank'] <= k for row in positives)
                            for k in (1, 8, 16, 32)},
                   'scope': contract['scope']}
        (args.output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        print(json.dumps(summary), flush=True)
    finally:
        recognizer.close()


if __name__ == '__main__':
    main()
