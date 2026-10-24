"""Public-only binding. No private path is inspected during preparation."""
import argparse
import copy
import platform
from pathlib import Path
import binding as b
FILES=('binding.py','parent_receipts.py','allocation.py','run.py','report.py','supervise.py','make_contract.py',
       'test_allocation.py','test_execution.py','test_supervise.py','DRAFT.md','DRAFT-NEXT.md','proof.py','test_proof.py','FREEZE.md')
WORK='/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1'

def build():
    b.require_checks()
    public={rel:b.sha(b.LIT/rel) for rel in b.PUBLIC.values()}
    parents={n:b.read(b.LIT/b.PUBLIC[n+'contract']) for n in ('50','56','57','60','61')}
    evidence={n:b.read(b.LIT/b.PUBLIC[n]) for n in ('50','56','57','59','60','61')}
    code={};runtime={}
    for parent in parents.values():
        for key,dest in (('code_hashes',code),('runtime_files',runtime)):
            for rel,h in parent[key].items():
                assert rel not in dest or dest[rel]==h,'incompatible inherited pin'
                dest[rel]=h
    code.update(public)
    for name in FILES:
        path=b.HERE/name;code[str(path.relative_to(b.LIT))]=b.sha(path)
    for rel,h in code.items():assert b.sha(b.LIT/rel)==h,rel
    for path,h in runtime.items():assert b.sha(path)==h,path
    arms={n:{a['cohort']:a for a in evidence[n]['arms']} for n in evidence}
    private={role:{} for role in b.ROLES}
    for role in b.ROLES:
        for cohort in b.COHORTS:
            for rel in (b.SOURCES[cohort],b.POOLS[cohort]):private[role][rel]=parents['50']['private_files'][rel]
            private[role][b.PARENTS[role][cohort]]=arms['60'][cohort]['production_arm_sha256' if role=='production' else 'independent_receipt_sha256']
    result={'schema':'gamma.required-joint-path-cap.contract.v1','active':False,'work':WORK,
        'population':'fixed300_fit_only','capacity':256,'denominator':1000000,'k_values':list(range(257)),
        'fit_ids':parents['50']['fit_ids'],'source_hashes':parents['50']['source_hashes'],
        'limits':b.LIMITS,'python_bin':parents['56']['python_bin'],'python_version':parents['56']['python_version'],
        'public_files':public,'code_hashes':code,'runtime_files':runtime,'role_private_files':private,
        **{'parent'+n+'_arms':arms[n] for n in arms},
        'predictions':{'P1':'Required exact inherited identity, fresh coverage/allocation replay and domination.',
                       'P2':'At least one cohort has strict raw charge reduction versus61 at k3; uncertain.',
                       'P3':'Naming largest positive budget exceeds4; uncertain.',
                       'P4':'At least one cohort has strict raw charge reduction versus61 at k256; uncertain.',
                       'P5':'At least one cohort has a positive integer bound at k256; uncertain.'},
        'authority':'Item60 full-graph science inherited. Fresh forced-owner coverage and constrained allocation only.',
        'qualification':'Exact original13 reuse; unchanged-source item23 exit137 separate; no fresh jobs.'}
    b.public_inputs(result)
    return result


def activate(current,pending):
    b.exact(current,pending);assert pending['active'] is False
    value=copy.deepcopy(pending);value['active']=True;return value


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--activate',action='store_true');args=ap.parse_args()
    result=build()
    if args.activate:result=activate(result,b.read(b.HERE/'pending-contract.json'))
    target=b.HERE/('contract.json' if args.activate else 'pending-contract.json')
    b.write(target,result);print({'path':str(target),'sha256':b.sha(target),'active':result['active'],'private_inputs_opened':False})
