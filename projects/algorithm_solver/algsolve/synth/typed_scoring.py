"""Crash-safe development scoring of immutable, already-decided route outputs.

This module neither predicts nor repairs graphs. Resumption reuses committed
verdicts and executes only missing scores under the same candidate and decisions.
"""
from __future__ import annotations

import fcntl
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile

from . import typed_codec


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_bytes_once(path, data):
    """Publish complete bytes without overwriting any previous artifact."""
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix='.'+path.name+'-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)  # Atomic and exclusive on the same filesystem.
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        os.unlink(temporary)


def write_json_once(path, value):
    write_bytes_once(path, (json.dumps(value, indent=2, allow_nan=False)+'\n').encode())


def preserve_json(path, value):
    if path.exists():
        if json.loads(path.read_text()) != value:
            raise ValueError(f'Existing evidence differs: {path.name}')
    else:
        write_json_once(path, value)


def score_frozen(output, requests, candidate, routes, load_tests, score_result):
    """Retain each route verdict; require the full frozen denominator to return.

    Callbacks receive development cases only. The caller verifies the complete
    candidate environment before invoking this function and before publication.
    No scoring callback runs until all response and cohort checks have passed.
    """
    output = Path(output)
    directory = output/'scoring'
    directory.mkdir(exist_ok=True)
    with (directory/'lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError('Another scorer owns this run') from error
        return _score_locked(output, requests, candidate, routes, load_tests, score_result)


def _score_locked(output, requests, candidate, routes, load_tests, score_result):
    directory = output/'scoring'
    frozen = {name: sha(output/name) for name in ('candidate.json','captures.jsonl','setup.json','decisions.jsonl')}
    if json.loads((output/'candidate.json').read_text()) != candidate:
        raise ValueError('Candidate identity differs from frozen file')
    decisions = [json.loads(line) for line in (output/'decisions.jsonl').read_text().splitlines() if line.strip()]
    expected = [(p['uid'],p['learning_split']) for p in requests]
    if (not expected or len({uid for uid,_ in expected}) != len(expected) or
            any(split not in ('development_fit','development_audit') for _,split in expected)):
        raise ValueError('Invalid development cohort')
    if [(r['uid'],r['split']) for r in decisions] != expected:
        raise ValueError('Missing, duplicate, reordered or unexpected decisions')
    if len(routes) != len(set(routes)) or any(set(row['routes']) != set(routes) for row in decisions):
        raise ValueError('Frozen route denominator differs')
    seal = {'schema':'algsolve.typed-development-scoring.v1',
            'candidate_sha256':typed_codec.digest(candidate), 'frozen_files_sha256':frozen,
            'cases':[{'uid':p['uid'], 'split':p['learning_split'],
                      'independent_tests_sha256':p['provenance']['independent_tests_sha256']}
                     for p in requests], 'routes':list(routes), 'protected_scoring':False}
    preserve_json(directory/'seal.json', seal)
    allowed = {f'{i:04d}-{route}.json' for i in range(len(requests)) for route in routes}
    if {p.name for p in directory.glob('*.json')} - allowed - {'seal.json'}:
        raise ValueError('Unexpected score receipt')

    def check_frozen():
        if any(sha(output/name) != digest for name,digest in frozen.items()):
            raise ValueError('Frozen evidence changed during scoring')

    rows = []
    for i,(pair,decision) in enumerate(zip(requests,decisions)):
        tests = None
        results = {}
        for route in routes:
            check_frozen()
            path = directory/f'{i:04d}-{route}.json'
            binding = {'candidate_sha256':seal['candidate_sha256'], 'uid':pair['uid'],
                       'route':route, 'decision_sha256':typed_codec.digest(decision['routes'][route]),
                       'independent_tests_sha256':pair['provenance']['independent_tests_sha256']}
            if path.exists():
                receipt = json.loads(path.read_text())
                digest = receipt.pop('receipt_sha256')
                if digest != typed_codec.digest(receipt) or receipt['binding'] != binding:
                    raise ValueError('Score receipt identity or contents changed')
            else:
                if tests is None:
                    tests = load_tests(copy.deepcopy(pair))
                    if not tests or typed_codec.digest(tests) != binding['independent_tests_sha256']:
                        raise ValueError('Independent development scoring authority changed')
                check_frozen()
                result = score_result(copy.deepcopy(pair), copy.deepcopy(decision['routes'][route]), tests)
                check_frozen()
                receipt = {'binding':binding, 'result':result}
                if any(result.get(k) != v for k,v in decision['routes'][route].items()
                       if k != 'infrastructure_failure') or (
                           decision['routes'][route].get('infrastructure_failure') and not result.get('infrastructure_failure')):
                    raise ValueError('Independent scoring changed a frozen route decision')
                write_json_once(path, {**receipt, 'receipt_sha256':typed_codec.digest(receipt)})
            results[route] = receipt['result']
        rows.append({**decision, 'independent_tests_sha256':pair['provenance']['independent_tests_sha256'],
                     'routes':results})
    check_frozen()
    return rows
