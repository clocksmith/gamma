"""Public-only pending binding; exact-match false-to-true activation."""
import argparse
import copy
import json
from pathlib import Path
import common as c


def build():
    c.require_checks();parentpath=c.LIT/'fraction-primal-repair-v1/contract.json'
    publicpath=c.LIT/'fraction-primal-repair-v1/evidence/results.json'
    parent=json.loads(parentpath.read_text());public=json.loads(publicpath.read_text())
    assert public['complete'] is True and public['validation_loaded'] is False
    assert public['contract_sha256']==c.sha(parentpath)
    result={k:copy.deepcopy(parent[k]) for k in ('fit_ids','python_bin','versions','runtime_files','code_hashes',
            'private_files','pool','construction','decoder_dependency_bytes','decoder_source_files','offline_encoder_scope')}
    result.update(schema='gamma.direct-fraction-exchange.contract.v1',active=False,population='fixed300_fit_only',
                  parent_contract=str(parentpath.relative_to(c.LIT)),parent_contract_sha256=c.sha(parentpath),
                  parent_evidence=str(publicpath.relative_to(c.LIT)),parent_private_results='fraction-primal-repair/run-v1/results.json',
                  parent_pool={},parent_references={},expected_seed_entries={},
                  search={'seconds':600,'evaluations':50000,'epochs':12,'shortlist':4,'expected_free_slots':7},
                  limits={'arm_cores':{'R':[6],'naming':[7]},'address_space_bytes':8*1024**3,
                          'production_seconds':1200,'report_seconds':1200,'cleanup_seconds':10},
                  pre_freeze_audit={'private_inputs_opened':False,'synthetic_only':True})
    result['private_files'][result['parent_private_results']]=public['private_results_sha256']
    for cohort in ('R','naming'):
        arm=next(a for a in public['arms'] if a['cohort']==cohort)
        rel=f'fraction-primal-repair/run-v1/{cohort}/pool.json';result['parent_pool'][cohort]=rel
        result['private_files'][rel]=arm['pool_sha256'];result['parent_references'][cohort]={}
        result['expected_seed_entries'][cohort]=arm['witnesses']['seed']['entries']
        assert result['pool']['capacity']-result['expected_seed_entries'][cohort]==7
        for name in ('seed','warm','cold'):
            rel=f'fraction-primal-repair/run-v1/{cohort}/{name}/dictionary.json'
            result['parent_references'][cohort][name]=rel;result['private_files'][rel]=arm['witnesses'][name]['dictionary_sha256']
    for path in (parentpath,publicpath):result['code_hashes'][str(path.relative_to(c.LIT))]=c.sha(path)
    # Parent report helpers are independently reused for packet/metadata checks.
    path=c.LIT/'fraction-primal-repair-v1/report.py';result['code_hashes'][str(path.relative_to(c.LIT))]=c.sha(path)
    for path in sorted(c.HERE.iterdir()):
        if path.suffix=='.py' or path.name in ('DRAFT.md','FREEZE.md'):
            result['code_hashes'][str(path.relative_to(c.LIT))]=c.sha(path)
    result['runtime_files'][str(Path(result['python_bin']).resolve())]=c.sha(Path(result['python_bin']).resolve())
    result['offline_encoder_files']={str((c.LIT/rel).resolve()):h for rel,h in result['code_hashes'].items()
                                    if rel.endswith(('.py','.cjs')) and '/test_' not in rel}
    result['offline_encoder_files'].update({p:h for p,h in result['runtime_files'].items() if p.endswith(('.js','.cjs'))})
    result['offline_encoder_bytes']=sum(Path(path).stat().st_size for path in result['offline_encoder_files'])
    return result


def activate(current,pending):
    assert current==pending and pending['active'] is False,'reviewed pending contract drift'
    active=copy.deepcopy(pending);active['active']=True;return active


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--activate',action='store_true');args=ap.parse_args()
    current=build();pending=c.HERE/'pending-contract.json'
    if args.activate:value=activate(current,json.loads(pending.read_text()));path=c.HERE/'contract.json'
    else:value=current;path=pending
    c.write(path,value);print(json.dumps({'path':str(path),'sha256':c.sha(path),'active':value['active'],'private_inputs_opened':False}))


if __name__=='__main__':main()
