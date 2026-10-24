"""Prepare a synthetic-only spec, or run it after separate review/authorization.

--pin constructs invented source strings and hashes only, not pools, q or paths.
The deterministic q-generation algorithm is code-pinned; its realized vector
digest is first computed during the separately authorized timed measurement.
"""
import argparse
import gc
import hashlib
import heapq
import importlib
import io
import json
import os
from pathlib import Path
import random
import resource
import signal
import sys
import time
import unittest

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
ALPHABET = [chr(i) for i in range(32, 127)] + ['\n']
D = 1000000


class HardDeadline(BaseException):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixtures():
    rng = random.Random(50065)
    texts = {}
    for pair in range(150):
        prefix = ''.join(rng.choice(ALPHABET) for _ in range(65))
        for member in range(2):
            texts[f'{2*pair+member:04}'] = prefix + ''.join(rng.choice(ALPHABET) for _ in range(185))
    banned = set(texts.values()) | {text[3:-3] for text in texts.values()}
    yield 'paired_prefix_75k', texts, banned
    rng = random.Random(50112)
    texts = {}
    for owner, marker in enumerate('0123456789!@'):
        period = marker + ''.join(rng.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(11))
        texts[f'{owner:04}'] = (period * 84)[:1000]
    banned = set(texts.values()) | {text[3:-3] for text in texts.values()}
    yield 'repeated_one_owner_12k', texts, banned


def fixture_metadata(name, texts, banned):
    return {'name': name, 'programs': len(texts), 'characters': sum(map(len, texts.values())),
            'max_source_length': max(map(len, texts.values())), 'sources_sha256': digest(texts),
            'banned_sha256': digest(sorted(banned)), 'banned_entries': len(banned)}


def prepare():
    """No pool construction or q generation in this public-only preparation."""
    code = [HERE/'prototype.py', HERE/'test_prototype.py', HERE/'independent.py',
            HERE/'test_independent.py', HERE/'synthetic.py', HERE/'DRAFT.md',
            LIT/'all-substring-fraction-v1/implicit.py', LIT/'all-length-fraction-v1/pool.py']
    modules = [random, heapq, hashlib, json, importlib, resource, signal, unittest]
    runtime = {str(Path(sys.executable).resolve()): sha(Path(sys.executable).resolve())}
    for module in modules:
        path = Path(module.__file__).resolve()
        runtime[str(path)] = sha(path)
    return {'schema': 'gamma.potential-lift.synthetic.v1', 'synthetic_only': True,
            'private_inputs_opened': False, 'core': 6, 'address_space_bytes': 8*1024**3,
            'worker_seconds': 180, 'outer_seconds': 180, 'outer_kill_after_seconds': 10,
            'fixtures': [fixture_metadata(*row) for row in fixtures()],
            'fixture_seeds': {'paired_prefix_75k': 50065, 'repeated_one_owner_12k': 50112},
            'alphabet_sha256': digest(ALPHABET), 'seed_dictionary': 'all96 optional paid characters',
            'denominator': D, 'capacity': 256, 'k_values': list(range(257)),
            'q_generation': '(17*int(pid)+31*start+43*end+97*sorted_pool_id+23)%101*(D//4)',
            'q_vector_digest': 'computed during timed full-pool reconstruction, not during --pin',
            'pool_rule': 'all shared length>=2 excluding global bans, union all96 optional characters; no learned seed extras',
            'python_bin': str(Path(sys.executable).resolve()), 'python_version': sys.version,
            'code_hashes': {str(path.relative_to(LIT)): sha(path) for path in code},
            'runtime_hashes': runtime}


def generate_q(texts, pool):
    trie = {}
    for eid, word in enumerate(pool):
        node = trie
        for ch in word:
            node = node.setdefault(ch, {})
        node[None] = eid
    q = []
    transitions = 0
    for pid, text in sorted(texts.items()):
        for start in range(len(text)):
            node = trie
            for end in range(start+1, len(text)+1):
                transitions += 1
                node = node.get(text[end-1])
                if node is None:
                    break
                if None in node:
                    q.append((17*int(pid)+31*start+43*end+97*node[None]+23)%101*(D//4))
    return q, transitions


def write(path, value):
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')
    tmp.replace(path)


def measure():
    started = time.monotonic()
    def expired(signum, frame):
        raise HardDeadline('whole synthetic measurement exceeded 180 seconds')
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 180)
    output = HERE/'synthetic-results.json'
    receipt = {'complete': False, 'synthetic_only': True, 'private_inputs_opened': False,
               'fixtures': [], 'phase': 'preflight'}
    fresh = False
    try:
        if not __debug__:
            raise RuntimeError('optimized Python is not allowed')
        os.sched_setaffinity(0, {6})
        resource.setrlimit(resource.RLIMIT_AS, (8*1024**3, 8*1024**3))
        assert not output.exists(), 'existing receipt must be preserved'
        fresh = True
        spec_path = HERE/'synthetic-spec.json'
        spec = json.loads(spec_path.read_text())
        assert prepare() == spec, 'spec/code/runtime/invented fixture drift'
        receipt['spec_sha256'] = sha(spec_path)
        receipt['code_hashes'] = spec['code_hashes']
        receipt['runtime_hashes'] = spec['runtime_hashes']
        import prototype as p
        import independent
        for name, texts, banned in fixtures():
            row = fixture_metadata(name, texts, banned)
            receipt['fixtures'].append(row)
            receipt['phase'] = name+':pool'
            begin = time.monotonic()
            pool = sorted(set(p.full._suffix.build_pool(texts, banned)) | set(ALPHABET))
            row.update(pool_seconds=time.monotonic()-begin, pool_entries=len(pool),
                       pool_string_bytes=sum(len(v.encode()) for v in pool), pool_sha256=digest(pool))
            receipt['phase'] = name+':q'
            begin = time.monotonic()
            q, transitions = generate_q(texts, pool)
            row.update(q_generation_seconds=time.monotonic()-begin, old_occurrences=len(q),
                       q_generation_trie_transitions=transitions, q_sha256=digest(q))
            receipt['phase'] = name+':old_replay_and_index'
            begin = time.monotonic()
            lift = p.Lift(texts, banned, pool, q, ALPHABET, ALPHABET, D,
                          old_source_hashes=p.source_hashes(texts), old_banned=banned)
            row.update(old_replay_and_index_seconds=time.monotonic()-begin,
                       full_groups=len(lift.index.groups),
                       full_distinct_entries=lift.index.distinct_allowed_entries)
            receipt['phase'] = name+':exact_aggregation_all_k'
            begin = time.monotonic()
            certificate = lift.certificate(256)
            row.update(aggregation_seconds=time.monotonic()-begin,
                       old_numerator=certificate['old_numerator'], old_charge=certificate['old_charge'],
                       path_numerator=sum(certificate['path_numerators'].values()),
                       class_counts=certificate['class_counts'],
                       repeated_occurrence_work=certificate['repeated_occurrence_work'],
                       unique_range_queries=certificate['unique_range_queries'],
                       unique_entries_extracted=certificate['unique_entries_extracted'],
                       old_trie_transitions=certificate['old_trie_transitions'],
                       occurrence_sha256=certificate['occurrence_sha256'], rows=certificate['rows'])
            assert row['old_trie_transitions'] == transitions
            assert len(row['rows']) == 257
            if name == 'repeated_one_owner_12k':
                assert row['repeated_occurrence_work'] > 0
            else:
                assert row['unique_entries_extracted'] > 0
            receipt['phase'] = name+':independent_all_depth_replay'
            begin = time.monotonic()
            checked = independent.check(texts, banned, pool, q, ALPHABET, ALPHABET, D,
                        expected_source_hashes=p.source_hashes(texts), expected_old_banned=banned,
                        expected_occurrence_sha256=certificate['occurrence_sha256'])
            for key in ('denominator', 'path_numerators', 'old_charge', 'old_numerator',
                        'class_counts', 'rows', 'top_entries', 'old_occurrences', 'occurrence_sha256'):
                assert checked[key] == certificate[key], ('independent disagreement', key)
            row.update(independent_seconds=time.monotonic()-begin,
                       independent_all257_agree=True,
                       independent_streamed_allowed_depths=checked['streamed_allowed_depths'],
                       independent_new_occurrence_contributions=checked['new_occurrence_contributions'],
                       independent_old_bellman_edges=checked['old_bellman_edges_checked'],
                       independent_tight_suffix_positions=checked['tight_suffix_positions_checked'])
            row['complete'] = True
            print(json.dumps({'fixture': name, 'phase': 'complete', 'elapsed_seconds': time.monotonic()-started,
                              'pool_entries': len(pool), 'old_occurrences': len(q),
                              'repeated_occurrence_work': row['repeated_occurrence_work']}), flush=True)
            del lift, q, pool, certificate, checked, texts, banned
            gc.collect()
        receipt['phase'] = 'small_independent_oracles'
        begin = time.monotonic()
        suite = unittest.defaultTestLoader.loadTestsFromNames(['test_prototype', 'test_independent'])
        result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
        assert result.wasSuccessful(), 'independent invented oracle checks failed'
        receipt['oracle_tests'] = result.testsRun
        receipt['oracle_seconds'] = time.monotonic()-begin
        receipt.update(complete=True, phase='complete', seconds=time.monotonic()-started,
                       peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        assert receipt['seconds'] <= 180
        write(output, receipt)
        assert time.monotonic()-started <= 180
        print(json.dumps({'complete': True, 'seconds': receipt['seconds'], 'sha256': sha(output)}))
    except BaseException as error:
        signal.setitimer(signal.ITIMER_REAL, 10)
        if fresh:
            receipt.update(complete=False, error=type(error).__name__+': '+str(error),
                           seconds=time.monotonic()-started,
                           peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            write(output, receipt)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--pin', action='store_true')
    mode.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if args.pin:
        value = prepare(); path = HERE/'synthetic-spec.json'; write(path, value)
        print(json.dumps({'prepared_only': True, 'sha256': sha(path), 'fixtures': value['fixtures']}))
    else:
        measure()
