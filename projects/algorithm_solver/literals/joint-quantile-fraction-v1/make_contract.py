"""Prepare public-only binding; activation must exactly match reviewed pending."""
import argparse
import copy
import json
from pathlib import Path
import common


def build():
    common.mechanism.parent.require_checks();lit=common.LIT;here=common.HERE
    parent_path=lit/'length-sensitive-fraction-v1/contract.json'
    evidence_path=lit/'length-sensitive-fraction-v1/evidence/results.json'
    parent=json.loads(parent_path.read_text());public=json.loads(evidence_path.read_text())
    assert public['complete'] is True and public['validation_loaded'] is False
    assert public['contract_sha256']==common.sha(parent_path)
    c={'schema':'gamma.joint-quantile-fraction.contract.v1','active':False,'population':'fixed300_fit_only',
       'fit_ids':parent['fit_ids'],'pool':parent['pool'],'denominator':parent['search']['denominator'],
       'scales':[list(s) for s in common.SCALES],'python_bin':parent['python_bin'],'versions':parent['versions'],
       'parent_contract_sha256':common.sha(parent_path),'parent_evidence':str(evidence_path.relative_to(lit)),
       'parent_recorded_commit':'a0f43fc3b','qualification':'binding-descent-v1/evidence/results.json',
       'sources':{},'parent_q':{},'private_files':{},'code_hashes':copy.deepcopy(parent['code_hashes']),
       'runtime_files':copy.deepcopy(parent['runtime_files']),
       'limits':{'arm_cores':{'R':[4],'naming':[5]},'address_space_bytes':8*1024**3,
                 'production_seconds':1200,'report_seconds':1200,'cleanup_seconds':10},
       'pre_freeze_audit':{'private_inputs_opened':False,'synthetic_only':True}}
    for cohort in ('R','naming'):
        prior=next(a for a in public['arms'] if a['cohort']==cohort)
        source=parent['cohorts'][cohort]+'/fit-sources.json'
        qfile=f'length-sensitive-fraction/run-v1/{cohort}-flex256/certificate-q.json'
        c['sources'][cohort]=source;c['parent_q'][cohort]=qfile
        c['private_files'][source]=prior['fit_source_sha256'];c['private_files'][qfile]=prior['certificate']['q_sha256']
    for path in (parent_path,evidence_path,lit/c['qualification']):c['code_hashes'][str(path.relative_to(lit))]=common.sha(path)
    for path in sorted(here.iterdir()):
        if path.suffix=='.py' or path.name in ('DRAFT.md','FREEZE.md'):
            c['code_hashes'][str(path.relative_to(lit))]=common.sha(path)
    c['runtime_files'][str(Path(c['python_bin']).resolve())]=common.sha(Path(c['python_bin']).resolve())
    return c


def activate(current,pending):
    assert current==pending and pending['active'] is False,'reviewed pending contract drift'
    result=copy.deepcopy(pending);result['active']=True;return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--activate',action='store_true');args=ap.parse_args()
    current=build();pending=common.HERE/'pending-contract.json'
    if args.activate:
        c=activate(current,json.loads(pending.read_text()));path=common.HERE/'contract.json'
    else:c=current;path=pending
    common.write(path,c);print(json.dumps({'path':str(path),'sha256':common.sha(path),'private_inputs_opened':False,'active':c['active']}))


if __name__=='__main__':main()
