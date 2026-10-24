"""Public-only pending binding; activation flips only the reviewed active bit."""
import argparse
import copy
import importlib
import json
from pathlib import Path
import platform
import sys
import binding as b


def check_synthetic_receipts(spec, receipt, supervisor, spec_sha):
    """Both completed phases bind the measured result; bool exit0 is invalid."""
    assert spec['whole_seconds'] == 180
    assert receipt['complete'] is supervisor['complete'] is True
    assert receipt['synthetic_only'] is supervisor['synthetic_only'] is True
    assert receipt['private_inputs_opened'] is False and receipt['phase'] == 'complete'
    assert receipt['spec_sha256'] == supervisor['spec_sha256'] == spec_sha
    assert type(supervisor['exit_code']) is int and supervisor['exit_code'] == 0
    result_seconds = b.number(receipt['seconds'], 180)
    supervisor_seconds = b.number(supervisor['seconds'], 180)
    assert result_seconds <= supervisor_seconds
    assert b.number(receipt['normal_cleanup_seconds'], 10) == b.number(supervisor['normal_cleanup_seconds'], 10)
    assert [row['name'] for row in receipt['fixtures']] == [row['name'] for row in spec['inputs']['fixtures']]
    for row in receipt['fixtures']:
        assert row['complete'] is row['independent_both257_agree'] is row['independent_both_top_identities_agree'] is True
        assert row['historical50_saved_fields_agree'] is True


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
    result = {'schema': 'gamma.potential-tightening.contract.v1', 'active': False,
              'population': 'fixed300_fit_only', 'fit_ids': c28['fit_ids'],
              'capacity': 256, 'denominator': 1000000, 'k_values': list(range(257)),
              'limits': copy.deepcopy(b.LIMITS), 'python_bin': c28['python_bin'],
              'versions': c28['versions'], 'cohorts': {}, 'private_files': {}, 'old_arms': {},
              'source_hashes': {}, 'full_shape': {}, 'public_files': public_files,
              'parent_contracts': {k: {'path': name+'/contract.json',
                                     'sha256': public_files[name+'/contract.json']} for k, name in parent_names.items()},
              'old_private_results': 'all-length-fraction/run-v1/results.json',
              'predictions': {'P1': 'required true: exact28/50 replay, fixed suffix potentials and all257 dominance',
                              'P2': 'uncertain: some cohort/k has strict raw charge reduction',
                              'P3': 'uncertain: some cohort largest-positive-k increases',
                              'P4': 'uncertain: some cohort positive at k256'},
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
    # Public-only50 prerequisite. No private50 paths or results enter the allowlist.
    cp = b.LIT/'potential-lift-certificate-v1/contract.json'
    ep = b.LIT/'potential-lift-certificate-v1/evidence/results.json'
    parent50, evidence50 = json.loads(cp.read_text()), json.loads(ep.read_text())
    result['parent50_contract'] = {'path': str(cp.relative_to(b.LIT)), 'sha256': b.sha(cp)}
    result['parent50_evidence'] = {'path': str(ep.relative_to(b.LIT)), 'sha256': b.sha(ep)}
    public_files[str(cp.relative_to(b.LIT))] = b.sha(cp)
    public_files[str(ep.relative_to(b.LIT))] = b.sha(ep)
    result['parent50_arms'] = {row['cohort']: row for row in evidence50['arms']}
    b.accepted_parent50(result, parent50, evidence50)
    spec = json.loads((b.HERE/'synthetic-spec.json').read_text())
    receipt = json.loads((b.HERE/'synthetic-results.json').read_text())
    supervisor = json.loads((b.HERE/'synthetic-supervisor.json').read_text())
    check_synthetic_receipts(spec, receipt, supervisor, b.sha(b.HERE/'synthetic-spec.json'))
    for rel, expected in spec['code_hashes'].items(): assert b.sha(b.LIT/rel) == expected
    result['code_hashes'] = dict(spec['code_hashes']) | public_files
    for path in b.HERE.iterdir():
        if path.suffix == '.py' or path.name in ('FREEZE.md', 'synthetic-spec.json', 'synthetic-results.json', 'synthetic-supervisor.json'):
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
