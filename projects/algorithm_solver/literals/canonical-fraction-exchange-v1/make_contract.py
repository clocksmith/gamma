"""Public-metadata-only binding; exact reviewed pending activation."""
import argparse
import copy
import json
from pathlib import Path
import common as c


def build():
    c.require_checks();priorpath=c.LIT/'direct-fraction-exchange-v1/contract.json'
    prior=json.loads(priorpath.read_text());primarypath=c.LIT/'direct-fraction-exchange-v1/evidence/results.json'
    shadowpath=c.LIT/'direct-fraction-exchange-v1/evidence/canonical-shadow.json'
    primary=json.loads(primarypath.read_text());shadow=json.loads(shadowpath.read_text())
    assert primary['complete'] is shadow['complete'] is True and primary['validation_loaded'] is shadow['validation_loaded'] is False
    assert primary['contract_sha256']==shadow['contract_sha256']==c.sha(priorpath)
    assert shadow['accepted_primary_report_sha256']==c.sha(primarypath)
    spec=json.loads((c.HERE/'synthetic-spec.json').read_text());receipt=json.loads((c.HERE/'synthetic-results.json').read_text())
    for name,h in spec['code_hashes'].items():assert c.sha(c.HERE/name)==h
    assert receipt['complete'] is True and receipt['spec_sha256']==c.sha(c.HERE/'synthetic-spec.json')
    assert spec['parent44_contract_sha256']==c.sha(priorpath)
    result=copy.deepcopy(prior)
    result.update(schema='gamma.canonical-fraction-exchange.contract.v1',active=False,
                  path_policy='minimum_N_then_complete_sorted_subset_ID_sequence',
                  objective='lex(exact_C_over_N,N,full_package)',canonical_parent_evidence=str(shadowpath.relative_to(c.LIT)),
                  canonical_seed_caps={},parent44_record_commit='07d99f2f2',
                  limits={'arm_cores':{'R':[4],'naming':[5]},'address_space_bytes':8*1024**3,
                          'production_seconds':1200,'report_seconds':1200,'cleanup_seconds':10},
                  pre_freeze_audit={'private_inputs_opened':False,'synthetic_only':True})
    assert result['search']=={'seconds':600,'evaluations':50000,'epochs':12,'shortlist':4,'expected_free_slots':7}
    for cohort in ('R','naming'):
        for name in ('warm','cold'):
            rel=result['parent_references'][cohort].pop(name);result['private_files'].pop(rel)
        arm=next(a for a in shadow['arms'] if a['cohort']==cohort)
        seed=arm['witnesses']['seed']['canonical_min_N'];assert seed['selections']['n']==300
        assert arm['original_parent_seed_dictionary_sha256']==result['private_files'][result['parent_references'][cohort]['seed']]
        result['canonical_seed_caps'][cohort]={pid:{'source_sha256':row['source_sha256'],'N':row['N']} for pid,row in seed['per_problem'].items()}
        assert set(result['canonical_seed_caps'][cohort])==set(map(str,result['fit_ids']))
    for path in (priorpath,primarypath,shadowpath):result['code_hashes'][str(path.relative_to(c.LIT))]=c.sha(path)
    for path in sorted(c.HERE.iterdir()):
        if path.suffix in ('.py','.md') or path.name in ('synthetic-spec.json','synthetic-results.json'):
            result['code_hashes'][str(path.relative_to(c.LIT))]=c.sha(path)
    result['offline_encoder_files']={str((c.LIT/rel).resolve()):h for rel,h in result['code_hashes'].items()
                                    if rel.endswith(('.py','.cjs')) and '/test_' not in rel}
    result['offline_encoder_files'].update({p:h for p,h in result['runtime_files'].items() if p.endswith(('.js','.cjs'))})
    result['offline_encoder_bytes']=sum(Path(p).stat().st_size for p in result['offline_encoder_files'])
    for rel,h in result['code_hashes'].items():assert c.sha(c.LIT/rel)==h,rel
    for path,h in result['runtime_files'].items():assert c.sha(path)==h,path
    return result


def activate(current,pending):
    assert current==pending and pending['active'] is False,'reviewed pending contract drift'
    for rel,h in pending['code_hashes'].items():assert c.sha(c.LIT/rel)==h
    for path,h in pending['runtime_files'].items():assert c.sha(path)==h
    active=copy.deepcopy(pending);active['active']=True;return active


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--activate',action='store_true');args=ap.parse_args();current=build()
    if args.activate:value=activate(current,json.loads((c.HERE/'pending-contract.json').read_text()));path=c.HERE/'contract.json'
    else:value=current;path=c.HERE/'pending-contract.json'
    c.write(path,value);print({'path':str(path),'sha256':c.sha(path),'active':value['active'],'private_inputs_opened':False})
