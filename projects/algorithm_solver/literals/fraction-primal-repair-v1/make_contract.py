"""Public metadata only; default writes an explicitly non-executable draft."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main(bind_parent_commit=None):
    parent_path = LIT / 'length-sensitive-fraction-v1/contract.json'
    parent = json.loads(parent_path.read_text())
    solver = json.loads((LIT / 'seeded-repair-v1/contract.json').read_text())
    c = {k: copy.deepcopy(parent[k]) for k in ('cohorts', 'fit_ids', 'python_bin', 'decoder_dependency_bytes',
         'decoder_source_files', 'offline_encoder_scope')}
    c.update(schema='gamma.fraction-primal-repair.contract.v1', ready_to_freeze=bool(bind_parent_commit),
             parent_recorded_commit=bind_parent_commit,
             parent_contract_sha256=sha(parent_path), parent_evidence='length-sensitive-fraction-v1/evidence/results.json',
             parent_private_results='length-sensitive-fraction/run-v1/results.json',
             parent_q={p: f'length-sensitive-fraction/run-v1/{p}-flex256/certificate-q.json' for p in ('R', 'naming')},
             parent_seed={p: f'length-sensitive-fraction/run-v1/{p}-flex256/seed/dictionary.json' for p in ('R', 'naming')},
             pool={'capacity': 256, 'entries': 2048, 'denominator': 1_000_000,
                   'scope': 'bounded proposed subset of all allowed exact substrings; relaxation witnesses only',
                   'protected': 'measured35 seed plus shortest/longest top256 realizations',
                   'path_ranking': 'descending use*(9*length+1) for length>1, zero singleton; descending owners; increasing length; string'},
             construction={'max_arcs': 1_000_000, 'max_transitions': 20_000_000, 'max_pool_characters': 2_000_000},
             search={'seconds': 600, 'random_seed': 400, 'threads': 1, 'mip_rel_gap': 0},
             solve_order={'R': ['warm', 'cold'], 'naming': ['cold', 'warm']},
             limits={'workers': 2, 'arm_cores': {'R': [14], 'naming': [15]}, 'address_space_bytes': 8 * 1024**3,
                     'cohort_seconds': 2400, 'overall_seconds': 2500},
             private_files={parent['cohorts'][p] + '/fit-sources.json': parent['private_files'][parent['cohorts'][p] + '/fit-sources.json'] for p in ('R', 'naming')},
             code_hashes={**solver['code_hashes'], **parent['code_hashes']},
             runtime_files={**solver['runtime_files'], **parent['runtime_files']},
             versions=solver['versions'], pre_freeze_audit={'private_inputs_opened': False, 'synthetic_only': True},
             predictions={'P1': 'warm full coverage with F no greater than measured seed, or explicit failure',
                          'P2': 'cold may fail to produce coverage under the same model and budget; no direction asserted',
                          'P3': 'no <=10% witness predicted; report outcome without M1 promotion'})
    assert solver['python_bin'] == parent['python_bin']
    for key, value in parent['versions'].items():
        assert solver['versions'][key] == value
    if bind_parent_commit:
        public_path = LIT / c['parent_evidence']; public = json.loads(public_path.read_text())
        assert public['complete'] is True and public['validation_loaded'] is False
        assert public['contract_sha256'] == sha(parent_path)
        c['private_files'][c['parent_private_results']] = public['private_results_sha256']
        assert len(public['arms']) == 2 and {a['cohort'] for a in public['arms']} == {'R', 'naming'}
        for arm in public['arms']:
            cohort = arm['cohort']
            c['private_files'][c['parent_q'][cohort]] = arm['certificate']['q_sha256']
            c['private_files'][c['parent_seed'][cohort]] = arm['witnesses']['seed']['dictionary_sha256']
        c['code_hashes'][c['parent_evidence']] = sha(public_path)
        diagnostic_path = LIT / 'length-sensitive-fraction-v1/evidence/bin-diagnostics.json'
        diagnostic = json.loads(diagnostic_path.read_text())
        assert diagnostic['complete'] is True and diagnostic['validation_loaded'] is False
        assert diagnostic['main_evidence_sha256'] == sha(public_path)
        assert diagnostic['private_results_sha256'] == public['private_results_sha256']
        assert diagnostic['contract_sha256'] == sha(parent_path)
        c['parent_bin_diagnostic'] = str(diagnostic_path.relative_to(LIT))
        c['code_hashes'][c['parent_bin_diagnostic']] = sha(diagnostic_path)
        c['adaptive_start'] = {
            'parent_bounds': {a['cohort']: a['certificate']['integer_lower_bound'] for a in public['arms']},
            'rounded_proposals': sum(a['primal_attempts'] for a in public['arms']),
            'rounded_proposals_infeasible': sum(a['primal_infeasible'] for a in public['arms']),
            'final_selected_bin_diagnostics': {a['cohort']: {k: a[k] for k in (
                'selected_entries', 'positive_weight_selected_entries', 'cutoff_selection_nonunique', 'upper_two_bins')}
                for a in diagnostic['arms']},
            'interpretation': 'No observed long-bin selection dominance; coverage-preserving primal construction remains unresolved.'}
    else:
        c['unbound_inputs'] = [c['parent_private_results'], *c['parent_q'].values(), *c['parent_seed'].values()]
    for rel in ('length-sensitive-fraction-v1/contract.json', 'seeded-repair-v1/contract.json'):
        c['code_hashes'][rel] = sha(LIT / rel)
    for path in HERE.iterdir():
        if path.suffix == '.py' and path.name != 'report.py' or path.name in ('DRAFT.md', 'FREEZE.md'):
            c['code_hashes'][str(path.relative_to(LIT))] = sha(path)
    c['offline_encoder_files'] = {str((LIT / rel).resolve()): value for rel, value in c['code_hashes'].items()
                                  if rel.endswith(('.py', '.cjs')) and '/test_' not in rel}
    c['offline_encoder_files'].update({p: h for p, h in c['runtime_files'].items() if p.endswith(('.js', '.cjs'))})
    c['offline_encoder_bytes'] = sum(Path(p).stat().st_size for p in c['offline_encoder_files'])
    (HERE / 'contract.json').write_text(json.dumps(c, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'contract_sha256': sha(HERE / 'contract.json'), 'ready_to_freeze': c['ready_to_freeze'], 'private_inputs_opened': False}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--bind-parent-commit'); a = p.parse_args(); main(a.bind_parent_commit)
