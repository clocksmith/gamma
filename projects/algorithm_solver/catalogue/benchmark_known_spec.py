"""Bounded receipt-bound artifact delivery timing, not full goal-1c qualification.

No model, candidate, or source-body output. Configuration is operator-trusted;
metadata/protection, receipt bindings and per-artifact hashing remain on-path.
"""
import argparse
import hashlib
import json
import math
import statistics
import sys
import time
from pathlib import Path
from .known_spec_service import KnownSpecService


def distribution(values):
    if not values:
        return {'count': 0, 'median_seconds': None, 'p95_seconds': None}
    ordered = sorted(values)
    return {'count': len(values), 'median_seconds': statistics.median(ordered),
            'p95_seconds': ordered[math.ceil(.95 * len(ordered)) - 1]}


def benchmark(path, config_sha256, *, max_requests=1000, max_wall=60):
    if type(max_requests) is not int or not 1 <= max_requests <= 10000:
        raise ValueError('bounded request count required')
    if type(max_wall) not in (int, float) or not 0 < max_wall <= 300:
        raise ValueError('bounded wall time required')
    start = time.perf_counter()
    service = KnownSpecService.from_config(path, config_sha256)
    initialized = time.perf_counter()
    # Reading metadata only; materialization still uses service authorization.
    ids = service._universe['eligible_problem_ids']
    selected = []
    for pid in ids:
        match = service.request(pid)
        if match['status'] != 'matched':
            continue
        for language in ('javascript', 'python'):
            choice = service.request(pid, language=language)
            if choice['status'] == 'matched':
                selected.append((pid, language))
    if len(selected) > max_requests:
        raise ValueError('full qualified-artifact traversal exceeds request cap')
    times = {'javascript': [], 'python': []}
    failures = []
    total_bytes = 0
    identities = []
    for pid, language in selected:
        if time.perf_counter() - start >= max_wall:
            raise TimeoutError('artifact delivery wall bound')
        before = time.perf_counter()
        answer = service.request(pid, language=language, include_source=True)
        elapsed = time.perf_counter() - before
        if answer['status'] != 'matched' or answer.get('artifact', {}).get('status') != 'materialized':
            failures.append({'problem_id': pid, 'language': language, 'reason': answer.get('reason', 'not materialized')})
            continue
        artifact = answer['artifact']
        data = artifact['source_utf8'].encode('utf-8')
        if len(data) != artifact['bytes'] or hashlib.sha256(data).hexdigest() != artifact['source_sha256']:
            raise ValueError('returned artifact identity mismatch')
        times[language].append(elapsed)
        total_bytes += len(data)
        identities.append([pid, language, artifact['source_sha256']])
    return {'schema': 'gamma.known-spec-delivery-timing.v1',
            'config_sha256': config_sha256, 'eligible_problems': len(ids),
            'python_version': sys.version.split()[0],
            'python_executable_sha256': hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
            'protected_id_count': len(service._universe['protected_problem_ids']),
            'qualified_artifacts_attempted': len(selected), 'failures': failures,
            'source_bytes_verified': total_bytes,
            'delivered_identity_digest': hashlib.sha256(json.dumps(identities, separators=(',', ':')).encode()).hexdigest(),
            'initialization_seconds': initialized - start,
            'total_seconds': time.perf_counter() - start,
            'per_language': {lang: distribution(values) for lang, values in times.items()},
            'scope': 'single-process sequential exact-ID artifact delivery; receipt validation at initialization, authorization and source hash per request',
            'cache_state': 'uncontrolled OS cache; not a cold-start claim',
            'excluded_stages': ['description encoding', 'recognition', 'query-public checks', 'candidate execution'],
            'candidate_executions': 0, 'goal_1c_qualified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = benchmark(args.config, args.config_sha256)
    with args.output.open('x') as file:
        json.dump(result, file, sort_keys=True, indent=2)
        file.write('\n')


if __name__ == '__main__':
    main()
