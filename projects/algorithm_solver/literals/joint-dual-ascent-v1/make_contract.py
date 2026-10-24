"""Public metadata only; activation must exactly match the reviewed pending file."""
import argparse
import copy
from pathlib import Path
import common as c


def build():
    parent_path=c.LIT/'joint-quantile-fraction-v1/contract.json';parent=c.read(parent_path)
    evidence_path=c.LIT/'joint-quantile-fraction-v1/evidence/results.json';public=c.read(evidence_path)
    assert public['complete'] is True and public['validation_loaded'] is False and public['contract_sha256']==c.sha(parent_path)
    spec=c.read(c.HERE/'synthetic-spec.json')
    for name,digest in spec['code_sha256'].items():assert c.sha(c.HERE/name)==digest
    assert c.sha(c.HERE/spec['measurement_receipt'])==spec['measurement_receipt_sha256']
    contract={'schema':'gamma.joint-dual-ascent.contract.v1','active':False,'population':'fixed300_fit_only',
              'fit_ids':parent['fit_ids'],'pool':parent['pool'],'denominator':parent['denominator'],
              'python_bin':parent['python_bin'],'versions':parent['versions'],'qualification':parent['qualification'],
              'sources':copy.deepcopy(parent['sources']),
              'private_files':{rel:parent['private_files'][rel] for rel in parent['sources'].values()},
              'parent_evidence':str(evidence_path.relative_to(c.LIT)),'parent_contract_sha256':c.sha(parent_path),
              'parent_recorded_commit':'0c840ac6a','baseline_numerators':{},
              'search':{'points':16,'initialization':'zero_only','step':'max(1,D//(4*ceil_sqrt(t+1)))','ties':'earliest_best'},
              'limits':{'arm_cores':{'R':[4],'naming':[5]},'address_space_bytes':8*1024**3,'endpoint_bytes':64*1024**2,
                        'production_seconds':1200,'report_seconds':1200,'cleanup_seconds':10},
              'code_hashes':copy.deepcopy(parent['code_hashes']),'runtime_files':copy.deepcopy(parent['runtime_files']),
              'pre_freeze_audit':{'private_inputs_opened':False,'synthetic_only':True}}
    for cohort in ('R','naming'):
        arm=next(a for a in public['arms'] if a['cohort']==cohort)
        assert arm['complete'] is True and arm['independent_cardinality_assignment_and_pool_replay'] is True
        assert arm['source_sha256']==contract['private_files'][contract['sources'][cohort]]
        zero=next(point for point in arm['points'] if point['scale']==[0,1])
        assert zero['quantiles_feasible_in_relaxed_pool'] is True
        contract['baseline_numerators'][cohort]=zero['joint_numerator']
    for path in (parent_path,evidence_path):contract['code_hashes'][str(path.relative_to(c.LIT))]=c.sha(path)
    for path in sorted(c.HERE.iterdir()):
        if path.suffix in ('.py','.md') or path.name in ('synthetic-spec.json','synthetic-complexity.json'):
            contract['code_hashes'][str(path.relative_to(c.LIT))]=c.sha(path)
    return contract


def activate(current,pending):
    assert current==pending and pending['active'] is False,'Pending contract drift'
    for rel,digest in pending['code_hashes'].items():assert c.sha(c.LIT/rel)==digest
    for path,digest in pending['runtime_files'].items():assert c.sha(path)==digest
    result=copy.deepcopy(pending);result['active']=True;return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--activate',action='store_true');args=ap.parse_args()
    current=build();path=c.HERE/('contract.json' if args.activate else 'pending-contract.json')
    if args.activate:current=activate(current,c.read(c.HERE/'pending-contract.json'))
    c.write(path,current);print({'path':str(path),'sha256':c.sha(path),'active':current['active'],'private_inputs_opened':False})
