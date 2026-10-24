"""Public-only pending binding; activation flips only the reviewed active bit."""
import argparse
import copy
import importlib
import json
from pathlib import Path
import platform
import sys
import binding as b


def build():
    b.require_checks()
    parent_names = {'28': 'all-length-fraction-v1', '33': 'all-substring-fraction-v1',
                    '35': 'length-sensitive-fraction-v1'}
    contracts, evidence, public_files = {}, {}, {}
    for number, name in parent_names.items():
        cp = b.LIT/name/'contract.json'; ep = b.LIT/name/'evidence/results.json'
        contracts[number] = json.loads(cp.read_text()); evidence[number] = json.loads(ep.read_text())
        public_files[str(cp.relative_to(b.LIT))] = b.sha(cp)
        public_files[str(ep.relative_to(b.LIT))] = b.sha(ep)
        assert evidence[number]['contract_sha256'] == b.sha(cp)
        assert evidence[number]['validation_loaded'] is False
    c28, c33, c35 = (contracts[k] for k in ('28', '33', '35'))
    assert evidence['33']['complete'] is evidence['35']['complete'] is True
    assert c28['fit_ids'] == c33['fit_ids'] == c35['fit_ids']
    assert c28['cohorts'] == c33['cohorts'] == c35['cohorts']
    assert len(c28['fit_ids']) == len(set(c28['fit_ids'])) == 300
    for rel in ('lagrange-select-v2/selection.py', 'tail-search-v1/structure.cjs',
                'cost-decomposition-v1/lexical.cjs'):
        assert c28['code_hashes'][rel] == c33['code_hashes'][rel] == c35['code_hashes'][rel] == b.sha(b.LIT/rel)
    qualification_path = b.LIT/'binding-descent-v1/evidence/results.json'
    public_files[str(qualification_path.relative_to(b.LIT))] = b.sha(qualification_path)
    qualification = json.loads(qualification_path.read_text())
    import numpy
    assert str(Path(sys.executable).absolute()) == c28['python_bin']
    assert c28['versions'] == {'numpy': numpy.__version__, 'python': platform.python_version()}
    result = {'schema': 'gamma.potential-lift.contract.v1', 'active': False,
              'population': 'fixed300_fit_only', 'fit_ids': c28['fit_ids'],
              'capacity': 256, 'denominator': 1000000, 'k_values': list(range(257)),
              'limits': copy.deepcopy(b.LIMITS), 'python_bin': c28['python_bin'],
              'versions': c28['versions'], 'cohorts': {}, 'private_files': {}, 'old_arms': {},
              'source_hashes': {}, 'full_shape': {}, 'public_files': public_files,
              'parent_contracts': {k: {'path': name+'/contract.json',
                                     'sha256': public_files[name+'/contract.json']} for k, name in parent_names.items()},
              'old_private_results': 'all-length-fraction/run-v1/results.json',
              'predictions': {'P1': 'required true: exact L28 and k0 dominance in both cohorts',
                              'P2': 'uncertain: some cohort positive at some k>=1',
                              'P3': 'predicted false: some cohort positive at k256'},
              'pre_freeze_audit': {'private_inputs_opened': False, 'synthetic_only': True}}
    result['private_files'][result['old_private_results']] = evidence['28']['private_results_sha256']
    for cohort in ('R', 'naming'):
        parent = next(a for a in evidence['28']['arms'] if a['cohort'] == cohort)
        full = next(a for a in evidence['35']['arms'] if a['cohort'] == cohort)
        assert parent['certificate_replayed'] is parent['pool_rebuilt'] is parent['body_audit_clean'] is True
        assert parent['capacity'] == 256 and parent['mandatory_entries'] == 0
        assert full['complete'] is True and full['validation_loaded'] is False
        root = c28['cohorts'][cohort]
        paths = {'sources': root+'/fit-sources.json', 'seed': root+'/dictionary.json',
                 'pool': f'all-length-fraction/run-v1/{cohort}-flex256/pool.json',
                 'q': f'all-length-fraction/run-v1/{cohort}-flex256/certificate-q.npy'}
        result['cohorts'][cohort] = paths
        for key in ('sources', 'seed'):
            rel = paths[key]
            assert c28['private_files'][rel] == c33['private_files'][rel] == c35['private_files'][rel]
            result['private_files'][rel] = c28['private_files'][rel]
        assert parent['fit_source_sha256'] == full['fit_source_sha256'] == result['private_files'][paths['sources']]
        result['private_files'][paths['pool']] = parent['pool_sha256']
        result['private_files'][paths['q']] = parent['optimization']['certificate']['q_sha256']
        old = {key: parent[key] for key in ('fit_source_sha256', 'pool_sha256', 'pool_entries',
               'maximum_entry_length', 'occurrences', 'shared_learned_entries', 'seed_extra_entries', 'seed_extras_sha256')}
        old['certificate'] = parent['optimization']['certificate']
        assert old['certificate']['denominator'] == 1000000 and old['certificate']['integer_lower_bound'] > 0
        result['old_arms'][cohort] = old
        result['full_shape'][cohort] = {'source_characters': full['source_characters'],
                     'full_groups': full['implicit_groups'], 'full_distinct_entries': full['pool_entries'],
                     'exact_ban_occurrences': full['exact_ban_occurrences']}
        arm = next(a for a in qualification['arms'] if a['arm'] == ('control' if cohort == 'R' else 'scope_joint') and a['width'] == 8)
        ids = set(map(str, c28['fit_ids']))
        assert ids <= set(arm['per_problem']) and all(arm['qualification'][pid]['passed'] is True for pid in ids)
        result['source_hashes'][cohort] = {pid: arm['per_problem'][pid]['source_sha256'] for pid in sorted(ids)}
    assert len(result['private_files']) == 9
    spec = json.loads((b.HERE/'synthetic-spec.json').read_text())
    receipt = json.loads((b.HERE/'synthetic-results.json').read_text())
    assert receipt['complete'] is True and receipt['spec_sha256'] == b.sha(b.HERE/'synthetic-spec.json')
    for rel, expected in spec['code_hashes'].items(): assert b.sha(b.LIT/rel) == expected
    result['code_hashes'] = dict(spec['code_hashes']) | public_files
    for path in b.HERE.iterdir():
        if path.suffix == '.py' or path.name in ('FREEZE.md', 'synthetic-spec.json', 'synthetic-results.json'):
            result['code_hashes'][str(path.relative_to(b.LIT))] = b.sha(path)
    for rel in ('tail-search-v1/structure.cjs', 'cost-decomposition-v1/lexical.cjs'):
        result['code_hashes'][rel] = b.sha(b.LIT/rel)
    runtime = dict(spec['runtime_hashes'])
    for path in ('/usr/bin/node', '/usr/share/nodejs/acorn/dist/acorn.js'):
        assert b.sha(path) == c28['runtime_files'][path]
        runtime[path] = b.sha(path)
    # Fixed dependency list, independent of modules a caller previously imported.
    for name in ('numpy', 'numpy._core._multiarray_umath', 'numpy._core.numeric',
                 'numpy._core.multiarray', 'numpy._core.overrides', 'numpy._utils',
                 'numpy.lib._npyio_impl', 'numpy.lib.format', 'numpy.lib._format_impl'):
        path = Path(importlib.import_module(name).__file__).resolve()
        runtime[str(path)] = b.sha(path)
    result['runtime_files'] = runtime
    return result


def activate(current, pending):
    assert current == pending and pending['active'] is False, 'reviewed pending drift'
    for rel, value in pending['code_hashes'].items(): assert b.sha(b.LIT/rel) == value
    for path, value in pending['runtime_files'].items(): assert b.sha(path) == value
    result = copy.deepcopy(pending); result['active'] = True
    return result


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--activate', action='store_true'); args = ap.parse_args()
    current = build()
    if args.activate:
        value = activate(current, json.loads((b.HERE/'pending-contract.json').read_text()))
        path = b.HERE/'contract.json'
    else:
        value = current; path = b.HERE/'pending-contract.json'
    b.write(path, value)
    print(json.dumps({'path': str(path), 'sha256': b.sha(path), 'active': value['active'], 'private_inputs_opened': False}))
