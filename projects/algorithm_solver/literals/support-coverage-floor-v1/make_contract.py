"""Public-only inactive binder; exact activation changes only active flag."""
import argparse
import copy
import json
from pathlib import Path
import binding as b


def build():
    b.require_checks()
    parent_rel='potential-lift-certificate-v1/contract.json'
    evidence_rel='potential-lift-certificate-v1/evidence/results.json'
    parent=b.read(b.LIT/parent_rel);evidence=b.read(b.LIT/evidence_rel)
    code=dict(parent['code_hashes']);runtime=dict(parent['runtime_files'])
    for rel,h in code.items():assert b.sha(b.LIT/rel)==h,rel
    for path,h in runtime.items():assert b.sha(path)==h,path
    code[parent_rel]=b.sha(b.LIT/parent_rel);code[evidence_rel]=b.sha(b.LIT/evidence_rel)
    for path in [*b.HERE.glob('*.py'),b.HERE/'DRAFT.md',b.HERE/'FREEZE.md']:
        code[str(path.relative_to(b.LIT))]=b.sha(path)
    cohorts={cohort:{key:parent['cohorts'][cohort][key] for key in ('sources','pool')} for cohort in b.COHORTS}
    private={rel:parent['private_files'][rel] for paths in cohorts.values() for rel in paths.values()}
    result={'schema':'gamma.support-coverage-floor.contract.v1','active':False,'population':'fixed300_fit_only',
        'fit_ids':parent['fit_ids'],'limits':b.LIMITS,'python_bin':parent['python_bin'],
        'python_version':parent['versions']['python'],'cohorts':cohorts,'private_files':private,
        'source_hashes':parent['source_hashes'],
        'parent50_contract':{'path':parent_rel,'sha256':code[parent_rel]},
        'parent50_evidence':{'path':evidence_rel,'sha256':code[evidence_rel]},
        'parent50_arms':{a['cohort']:a for a in evidence['arms']},
        'code_hashes':code,'runtime_files':runtime,
        'predictions':{'P1':'Required exact identity and independent reachability agreement.',
                       'P2':'Coverage floor exceeds item50 largest positive support budget in both cohorts; uncertain.'},
        'qualification':'Exact original item13 receipt reuse only; item23 unchanged-source exit137 remains separate.',
        'private_authority':'Exactly two fit-source JSON and two original28 pool JSON files; no q, seed, validation or cases.'}
    b.accepted_parent(result)
    return result


def activate(current,pending):
    b.exact(current,pending);assert pending['active'] is False
    for rel,h in pending['code_hashes'].items():assert b.sha(b.LIT/rel)==h
    for path,h in pending['runtime_files'].items():assert b.sha(path)==h
    value=copy.deepcopy(pending);value['active']=True;return value


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--activate',action='store_true');args=ap.parse_args()
    current=build()
    if args.activate:
        value=activate(current,b.read(b.HERE/'pending-contract.json'));path=b.HERE/'contract.json'
    else:value=current;path=b.HERE/'pending-contract.json'
    b.write(path,value);print(json.dumps({'path':str(path),'sha256':b.sha(path),'active':value['active'],'private_inputs_opened':False}))
