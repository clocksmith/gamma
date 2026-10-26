"""Bounded Node/browser model parity probe; never a recognition qualification."""
import argparse
import json
from pathlib import Path

import numpy as np

from .doppler_runtime import DopplerRuntime, sha

CASES = [
    ('pair', 'Find two positions in an integer array whose values sum to a target.',
     ['Return the indices of two array elements whose sum equals the target.',
      'Return the length of the longest increasing subsequence.']),
    ('islands', 'Count the connected groups of land in a binary grid using four-direction adjacency.',
     ['Return the number of four-connected islands in a grid of land and water.',
      'Return the maximum sum of a contiguous subarray.']),
    ('brackets', 'Determine whether parentheses and square and curly brackets are correctly nested and closed.',
     ['Check whether a string of brackets has matching opening and closing types in proper nesting order.',
      'Sort the integers of an array in ascending order.']),
]


def physical(backend):
    adapter = backend.get('adapter', {})
    text = json.dumps(adapter).lower()
    return (backend.get('backend') == 'webgpu' and bool(adapter)
            and not any(word in text for word in ('swiftshader', 'llvmpipe', 'software rasterizer')))


def run(args):
    config = json.loads(args.runtime_config.read_text()) if args.runtime_config else {}
    results, vectors = {}, {}
    for surface in ('node', 'browser'):
        with DopplerRuntime(args.doppler_root, args.embedding_model, args.reranker_model,
                            surface=surface, timeout=90, embedding_config=config.get('embedding'),
                            reranker_config=config.get('rerank')) as runtime:
            query, documents = CASES[0][1:]
            query_vector = runtime.encode([query], query=True)
            query_receipt = runtime.last_receipt
            document_vectors = runtime.encode(documents)
            document_receipt = runtime.last_receipt
            cases = []
            for ident, text, candidates in CASES:
                scores = runtime.rerank(text, candidates)
                cases.append({'id': ident, 'scores': scores, 'expected_first': scores[0] > scores[1],
                              'receipt': runtime.last_receipt})
            repeated = runtime.encode([query], query=True)
            vectors[surface] = np.concatenate([query_vector, document_vectors])
            backends = [row['backend'] for row in query_receipt['embedding_rows'] + document_receipt['embedding_rows']]
            backends += [case['receipt']['backend'] for case in cases]
            similarities = (document_vectors @ query_vector[0]).tolist()
            results[surface] = {
                'identity': runtime.identity, 'query_receipt': query_receipt,
                'document_receipt': document_receipt, 'cases': cases,
                'document_similarities': similarities,
                'embedding_expected_first': similarities[0] > similarities[1],
                'model_switch_embedding_max_abs': float(np.max(np.abs(repeated - query_vector))),
                'physical_gpu': all(physical(b) for b in backends),
            }
    vector_error = float(np.max(np.abs(vectors['node'] - vectors['browser'])))
    score_error = max(abs(a - b) for x, y in zip(results['node']['cases'], results['browser']['cases'])
                      for a, b in zip(x['scores'], y['scores']))
    passed = (vector_error <= 1e-5 and score_error <= 1e-3 and all(
        r['physical_gpu'] and r['embedding_expected_first'] and r['model_switch_embedding_max_abs'] <= 1e-5
        and all(c['expected_first'] for c in r['cases']) for r in results.values()))
    return {'schema': 'gamma.doppler-node-browser-probe.v1', 'passed': passed,
            'probe_sha256': sha(__file__), 'cases': CASES, 'surfaces': results,
            'embedding_max_abs_difference': vector_error, 'rerank_max_abs_difference': score_error,
            'recognition_qualified': False,
            'scope': 'Three synthetic integration probes; no catalogue, source, protected data or evaluation cohort read.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('doppler-root', 'embedding-model', 'reranker-model', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--runtime-config', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists; preserve earlier evidence')
    result = run(args)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('surfaces', 'cases')}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
