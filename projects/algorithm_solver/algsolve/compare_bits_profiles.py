"""Compare complete development profiles without promoting accuracy or latency claims."""
import argparse
import json
import math
from pathlib import Path


def read_profile(directory):
    contract = json.loads((directory/'contract.json').read_text())
    if contract.get('schema') != 'gamma.bits-profile.v1' or not 1 <= contract['repeats'] <= 5:
        raise ValueError('bounded BITS profile required')
    rows = [json.loads((directory/f'{i}.json').read_text()) for i in range(contract['repeats'])]
    if any(row.get('iteration') != i or 'error_type' in row or not row.get('diagnostics')
           for i, row in enumerate(rows)):
        raise ValueError('complete successful semantic profile required')
    return contract, rows


def compare(reference, candidate, tolerance=.02):
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError('finite nonnegative tolerance required')
    bc, br = reference
    cc, cr = candidate
    for key in ('keys_sha256', 'vectors_sha256', 'catalogue_sha256', 'packets_sha256', 'gate_sha256'):
        if bc['index'][key] != cc['index'][key]:
            raise ValueError('index mismatch: '+key)
    for role in ('embedding', 'rerank'):
        if bc['index']['runtime']['models'][role]['manifest_sha256'] != cc['index']['runtime']['models'][role]['manifest_sha256']:
            raise ValueError('model weights/template manifest changed')
    maximum = 0.
    ref = br[0]
    rank = lambda evidence: sorted(evidence, key=lambda r: (-(r['trueLogit']-r['falseLogit']), r['key']))
    for row in br+cr:
        if row['query_sha256'] != ref['query_sha256']:
            raise ValueError('query changed')
        left, right = ref['diagnostics']['evidence'], row['diagnostics']['evidence']
        if not left or len(left) != len(right):
            raise ValueError('candidate count changed')
        for a, b in zip(left, right):
            for key in ('key', 'document_sha256', 'document_scope', 'tokenIds', 'tokenCount'):
                if a[key] != b[key]:
                    raise ValueError('scored input changed: '+key)
            for key in ('trueLogit', 'falseLogit'):
                if not math.isfinite(a[key]) or not math.isfinite(b[key]):
                    raise ValueError('nonfinite logits')
                maximum = max(maximum, abs(a[key]-b[key]))
        if [r['key'] for r in rank(left)] != [r['key'] for r in rank(right)]:
            raise ValueError('candidate ranking changed')
    if maximum > tolerance:
        raise ValueError('logit tolerance exceeded')
    return {'schema': 'gamma.bits-profile-comparison.v1', 'recognition_qualified': False,
            'query_sha256': ref['query_sha256'], 'max_abs_logit_delta': maximum,
            'logit_tolerance': tolerance, 'executed_tokens_identical': True, 'all_rankings_identical': True,
            'reference_ms': [row['timings'] for row in br], 'candidate_ms': [row['timings'] for row in cr],
            'scope': 'One repeated development query; no population p50/p95, new calibration or recognition qualification.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(read_profile(args.reference), read_profile(args.candidate))
    with args.output.open('x') as stream:
        stream.write(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if not k.endswith('_ms')}))


if __name__ == '__main__':
    main()
