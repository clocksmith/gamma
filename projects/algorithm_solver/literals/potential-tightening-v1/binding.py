"""Public pin checks and activated, exact-nine-file input authority for item53."""
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
    assert c['schema'] == 'gamma.potential-tightening.contract.v1'
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
    verify_parent50(c)


def strict_equal(actual, expected):
    """JSON identity preserves numeric/bool distinctions in retained metadata."""
    assert json.dumps(actual, sort_keys=True, separators=(',', ':'), allow_nan=False) == json.dumps(
        expected, sort_keys=True, separators=(',', ':'), allow_nan=False)


def hash_value(value):
    assert type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def accepted_parent50(c, parent, evidence):
    """Pure public-metadata checks, shared by pending construction/preflight."""
    assert parent['active'] is True
    assert parent['schema'] == 'gamma.potential-lift.contract.v1'
    for field in ('population', 'fit_ids', 'capacity', 'denominator', 'k_values', 'limits',
                  'cohorts', 'private_files', 'old_private_results', 'old_arms', 'source_hashes', 'full_shape'):
        strict_equal(parent[field], c[field])
    assert evidence['schema'] == 'gamma.potential-lift.report.v1'
    assert evidence['contract_sha256'] == c['parent50_contract']['sha256']
    assert evidence['complete'] is True and evidence['validation_loaded'] is False
    assert not {'failure', 'failure_type'} & set(evidence)
    assert evidence['validation_or_cases_opened'] is False and evidence['population'] == 'fixed300_fit_only'
    assert evidence['predictions']['P1'] is True
    assert evidence['verdicts']['all257_replayed'] is evidence['verdicts']['k0_preserves_old_bound'] is True
    assert evidence['m1_claim'] is evidence['packet_or_witness_claim'] is evidence['optimality_claim'] is False
    assert type(evidence['arms']) is list and len(evidence['arms']) == 2
    assert [a['cohort'] for a in evidence['arms']] == ['R', 'naming']
    assert set(c['parent50_arms']) == {'R', 'naming'}
    for row in evidence['arms']:
        cohort = row['cohort']; old = c['old_arms'][cohort]; cert = old['certificate']
        strict_equal(c['parent50_arms'][cohort], row)
        assert row['schema'] == 'gamma.potential-lift.report-arm.v1'
        assert row['contract_sha256'] == c['parent50_contract']['sha256']
        assert row['complete'] is True and row['validation_loaded'] is False
        assert not {'failure', 'failure_type'} & set(row)
        assert row['all257_independently_replayed'] is row['old_certificate_independently_replayed'] is row['suffix_potential_proof_checked'] is True
        for field in ('bindings_sha256', 'source_identity_sha256', 'banned_set_sha256', 'parent_certificate_sha256',
                      'checked_proof_sha256', 'top_entries_sha256', 'old_occurrence_order_sha256', 'old_path_terms_sha256'):
            hash_value(row[field])
        assert row['source_identity_sha256'] == digest(c['source_hashes'][cohort])
        assert row['parent_certificate_sha256'] == digest(cert)
        assert row['old_path_terms_sha256'] == digest(cert['per_program_path_numerators'])
        strict_equal(row['geometry'], c['full_shape'][cohort])
        for field, expected in {'fit_problems': 300, 'denominator': c['denominator'],
             'old_pool_entries': old['pool_entries'], 'old_occurrences': old['occurrences'],
             'old_charge': cert['top_capacity_numerator'], 'path_numerator': cert['relaxed_paths_numerator'],
             'old_numerator': cert['numerator'], 'old_integer_lower_bound': cert['integer_lower_bound']}.items():
            assert type(row[field]) is int and row[field] == expected
        counts = row['class_counts']; assert set(counts) == {'1', '2'}
        assert all(type(n) is int and n >= 0 for n in counts.values())
        assert sum(counts.values()) == row['geometry']['full_distinct_entries']
        assert len(row['rows']) == 257
        for k, allocation in enumerate(row['rows']):
            assert set(allocation) == {'k', 'charge', 'one_owner_slots', 'shared_slots', 'numerator', 'integer_lower_bound'}
            assert all(type(n) is int for n in allocation.values())
            assert allocation['k'] == k and allocation['charge'] >= 0
            one, shared = allocation['one_owner_slots'], allocation['shared_slots']
            assert 0 <= one <= min(k, counts['1']) and 0 <= shared <= counts['2'] and one+shared <= 256
            assert allocation['numerator'] == row['path_numerator']-allocation['charge']
            assert allocation['integer_lower_bound'] == -(-allocation['numerator']//c['denominator'])
        assert all(a['charge'] <= b['charge'] for a, b in zip(row['rows'], row['rows'][1:]))
        assert row['rows'][0]['integer_lower_bound'] >= cert['integer_lower_bound']
        strict_equal(row['largest_positive_k'], max((a['k'] for a in row['rows'] if a['integer_lower_bound'] > 0), default=None))


def verify_parent50(c):
    named = {'parent50_contract': 'potential-lift-certificate-v1/contract.json',
             'parent50_evidence': 'potential-lift-certificate-v1/evidence/results.json'}
    values = {}
    for field, path in named.items():
        expected = c[field]
        assert expected == {'path': path, 'sha256': c['public_files'][path]}
        assert c['code_hashes'][path] == expected['sha256'] == sha(LIT/path)
        values[field] = json.loads((LIT/path).read_text())
    accepted_parent50(c, values['parent50_contract'], values['parent50_evidence'])


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
    assert digest(bindings) == c['parent50_arms'][cohort]['bindings_sha256']
    assert digest(sorted(banned)) == c['parent50_arms'][cohort]['banned_set_sha256']
    return {'texts': texts, 'banned': banned, 'pool': pool, 'q': q, 'seed': seed,
            'alphabet': ALPHABET, 'denominator': c['denominator'], 'source_hashes': source_hashes,
            'parent_certificate': expected['certificate'], 'geometry': c['full_shape'][cohort],
            'bindings': bindings}
