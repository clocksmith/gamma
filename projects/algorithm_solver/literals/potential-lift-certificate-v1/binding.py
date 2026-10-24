"""Public pin checks and activated, exact-nine-file input authority for item50."""
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
ALPHABET = [chr(i) for i in range(32, 127)] + ['\n']
LIMITS = {'worker_seconds': 600, 'production_seconds': 1200, 'report_seconds': 1200,
          'cleanup_seconds': 10, 'address_space_bytes': 8*1024**3,
          'arm_cores': {'R': [6], 'naming': [7]}}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def write(path, value):
    path = Path(path); tmp = path.with_name(path.name+'.tmp')
    with tmp.open('w') as stream:
        json.dump(value, stream, sort_keys=True, indent=2); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())
    os.replace(tmp, path)


def require_checks():
    if not __debug__ or sys.flags.optimize or 'PYTHONOPTIMIZE' in os.environ:
        raise RuntimeError('assertions required')


def number(value, maximum=None):
    assert type(value) in (int, float) and math.isfinite(value) and value >= 0
    assert maximum is None or value <= maximum
    return value


def check_contract(c):
    """Public/runtime checks only. Must precede any private open."""
    require_checks()
    assert c['active'] is True and c['population'] == 'fixed300_fit_only'
    assert c['limits'] == LIMITS and c['capacity'] == 256 and c['denominator'] == 1000000
    assert c['k_values'] == list(range(257))
    assert len(c['fit_ids']) == len(set(c['fit_ids'])) == 300
    assert str(Path(sys.executable).absolute()) == c['python_bin']
    assert platform.python_version() == c['versions']['python']
    assert all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'))
    for rel, expected in c['code_hashes'].items():
        assert sha(LIT/rel) == expected, rel
    for path, expected in c['runtime_files'].items():
        assert sha(path) == expected, path
    for rel, expected in c['public_files'].items():
        assert c['code_hashes'][rel] == expected == sha(LIT/rel), rel
    parents, evidence = {}, {}
    names = {'28': 'all-length-fraction-v1', '33': 'all-substring-fraction-v1',
             '35': 'length-sensitive-fraction-v1'}
    assert set(c['parent_contracts']) == set(names)
    for key, name in names.items():
        rel = name+'/contract.json'
        assert c['parent_contracts'][key] == {'path': rel, 'sha256': c['public_files'][rel]}
        parents[key] = json.loads((LIT/rel).read_text())
        evidence[key] = json.loads((LIT/name/'evidence/results.json').read_text())
        assert evidence[key]['contract_sha256'] == c['public_files'][rel]
        assert evidence[key]['validation_loaded'] is False
        assert parents[key]['fit_ids'] == c['fit_ids']
    assert evidence['33']['complete'] is evidence['35']['complete'] is True
    for rel in ('lagrange-select-v2/selection.py', 'tail-search-v1/structure.cjs', 'cost-decomposition-v1/lexical.cjs'):
        assert len({p['code_hashes'][rel] for p in parents.values()}) == 1
        assert parents['28']['code_hashes'][rel] == sha(LIT/rel)
    assert c['old_private_results'] == 'all-length-fraction/run-v1/results.json'
    assert c['private_files'][c['old_private_results']] == evidence['28']['private_results_sha256']
    qualification = json.loads((LIT/'binding-descent-v1/evidence/results.json').read_text())
    for cohort in ('R', 'naming'):
        paths = c['cohorts'][cohort]; root = parents['28']['cohorts'][cohort]
        assert all(p['cohorts'][cohort] == root for p in parents.values())
        assert paths == {'sources': root+'/fit-sources.json', 'seed': root+'/dictionary.json',
                         'pool': f'all-length-fraction/run-v1/{cohort}-flex256/pool.json',
                         'q': f'all-length-fraction/run-v1/{cohort}-flex256/certificate-q.npy'}
        for field in ('sources', 'seed'):
            assert all(p['private_files'][paths[field]] == c['private_files'][paths[field]] for p in parents.values())
        old = next(a for a in evidence['28']['arms'] if a['cohort'] == cohort)
        full = next(a for a in evidence['35']['arms'] if a['cohort'] == cohort)
        assert old['certificate_replayed'] is old['pool_rebuilt'] is old['body_audit_clean'] is True
        assert full['complete'] is True
        assert old['fit_source_sha256'] == full['fit_source_sha256'] == c['private_files'][paths['sources']]
        assert c['old_arms'][cohort]['certificate'] == old['optimization']['certificate']
        for field, value in c['old_arms'][cohort].items():
            if field != 'certificate': assert value == old[field], field
        assert c['private_files'][paths['pool']] == old['pool_sha256']
        assert c['private_files'][paths['q']] == old['optimization']['certificate']['q_sha256']
        assert c['full_shape'][cohort] == {'source_characters': full['source_characters'],
                    'full_groups': full['implicit_groups'], 'full_distinct_entries': full['pool_entries'],
                    'exact_ban_occurrences': full['exact_ban_occurrences']}
        qualified = next(a for a in qualification['arms'] if a['arm'] == ('control' if cohort == 'R' else 'scope_joint') and a['width'] == 8)
        assert all(qualified['qualification'][str(pid)]['passed'] is True for pid in c['fit_ids'])
        assert c['source_hashes'][cohort] == {str(pid): qualified['per_problem'][str(pid)]['source_sha256'] for pid in c['fit_ids']}
    import numpy
    assert numpy.__version__ == c['versions']['numpy']
    expected_paths = {c['old_private_results']}
    for row in c['cohorts'].values():
        expected_paths.update(row.values())
    assert set(c['cohorts']) == {'R', 'naming'}
    assert all(set(row) == {'sources', 'seed', 'pool', 'q'} for row in c['cohorts'].values())
    assert set(c['private_files']) == expected_paths and len(expected_paths) == 9
    assert all(not Path(p).is_absolute() and '..' not in Path(p).parts for p in expected_paths)


def checked_bytes(c, work, relative):
    assert c['active'] is True and relative in c['private_files']
    raw = (Path(work)/relative).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == c['private_files'][relative], relative
    return raw


def parse_bans(texts, deadline):
    """Same pinned parser as28/35; child inherits worker process group."""
    remaining = deadline-time.monotonic()
    if remaining <= 0:
        raise TimeoutError('ban-parser deadline')
    proc = subprocess.Popen(['/usr/bin/node', str(LIT/'tail-search-v1/structure.cjs')],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        out, err = proc.communicate(json.dumps(texts).encode(), timeout=remaining)
        assert proc.returncode == 0, 'pinned source/body parser failed'
    except BaseException:
        proc.kill()
        try: proc.wait(timeout=1)
        except subprocess.TimeoutExpired: pass
        raise
    parsed = json.loads(out)
    assert set(parsed) == set(texts)
    banned = set(texts.values())
    for row in parsed.values():
        assert isinstance(row, dict) and isinstance(row['bodies'], list) and row['bodies']
        assert all(type(word) is str and word for word in row['bodies'])
        banned.update(row['bodies'])
    return banned


def load_q(raw, expected_occurrences):
    import numpy as np
    stream = io.BytesIO(raw)
    q = np.load(stream, allow_pickle=False)
    assert isinstance(q, np.ndarray) and q.ndim == 1 and q.shape == (expected_occurrences,)
    assert q.dtype.kind == 'i' and q.dtype.itemsize == 8
    assert stream.tell() == len(raw), 'trailing q payload'
    values = q.tolist()
    assert all(type(v) is int and v >= 0 for v in values)
    return values


def load_inputs(c, work, cohort, deadline):
    check_contract(c)
    assert cohort in ('R', 'naming') and time.monotonic() < deadline
    paths = c['cohorts'][cohort]
    raw_parent = json.loads(checked_bytes(c, work, c['old_private_results']))
    assert raw_parent['contract_sha256'] == c['parent_contracts']['28']['sha256']
    assert raw_parent['validation_loaded'] is False
    assert len(raw_parent['arms']) == 2 and {a['cohort'] for a in raw_parent['arms']} == {'R', 'naming'}
    old = next(a for a in raw_parent['arms'] if a['cohort'] == cohort)
    expected = c['old_arms'][cohort]
    assert old['mode'] == 'flex256' and old['capacity'] == 256 and old['mandatory_entries'] == 0
    assert old['validation_loaded'] is False
    for key in ('fit_source_sha256', 'pool_sha256', 'pool_entries', 'maximum_entry_length',
                'occurrences', 'shared_learned_entries', 'seed_extra_entries', 'seed_extras_sha256'):
        assert old[key] == expected[key], key
    assert old['optimization']['certificate'] == expected['certificate']
    texts = json.loads(checked_bytes(c, work, paths['sources']))
    seed = json.loads(checked_bytes(c, work, paths['seed']))
    pool = json.loads(checked_bytes(c, work, paths['pool']))
    assert set(texts) == set(map(str, c['fit_ids'])) and all(type(t) is str and t for t in texts.values())
    assert set(''.join(texts.values())) <= set(ALPHABET)
    source_hashes = {pid: hashlib.sha256(t.encode()).hexdigest() for pid, t in texts.items()}
    assert source_hashes == c['source_hashes'][cohort]
    assert len(seed) == len(set(seed)) <= 256 and all(type(s) is str and s for s in seed)
    assert pool == sorted(set(pool)) and all(type(s) is str and s for s in pool)
    assert len(pool) == expected['pool_entries'] and max(map(len, pool)) == expected['maximum_entry_length']
    q = load_q(checked_bytes(c, work, paths['q']), expected['occurrences'])
    banned = parse_bans(texts, deadline)
    assert not set(pool) & banned and not set(seed) & banned
    assert set(seed) <= set(pool) and set(ALPHABET) <= set(pool)
    assert time.monotonic() < deadline
    bindings = {'source_sha256': c['private_files'][paths['sources']],
                'seed_sha256': c['private_files'][paths['seed']],
                'pool_sha256': c['private_files'][paths['pool']],
                'q_sha256': c['private_files'][paths['q']],
                'old_private_results_sha256': c['private_files'][c['old_private_results']],
                'source_hashes_sha256': digest(source_hashes),
                'bans_sha256': digest(sorted(banned)), 'banned_entries': len(banned),
                'old_evidence_sha256': c['public_files']['all-length-fraction-v1/evidence/results.json'],
                'full_evidence_sha256': c['public_files']['length-sensitive-fraction-v1/evidence/results.json']}
    return {'texts': texts, 'banned': banned, 'pool': pool, 'q': q, 'seed': seed,
            'alphabet': ALPHABET, 'denominator': c['denominator'], 'source_hashes': source_hashes,
            'parent_certificate': expected['certificate'], 'geometry': c['full_shape'][cohort],
            'bindings': bindings}
