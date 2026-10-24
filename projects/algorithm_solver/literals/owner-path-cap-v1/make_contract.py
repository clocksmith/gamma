"""Public-only inactive binding; no original inputs or private53 authority."""
import argparse
import copy
import json
from pathlib import Path
import binding as b


def check_synthetic_receipts(spec,result,supervisor,spec_sha):
    assert spec['whole_seconds']==180 and spec['synthetic_only'] is True and spec['private_inputs_opened'] is False
    assert result['schema']=='gamma.owner-path-cap.synthetic-result.v1'
    assert result['complete'] is supervisor['complete'] is True
    assert result['synthetic_only'] is supervisor['synthetic_only'] is True
    assert result['private_inputs_opened'] is False and result['phase']=='complete'
    assert result['spec_sha256']==supervisor['spec_sha256']==spec_sha
    assert result['input_spec_sha256']==spec['input_spec_sha256']
    assert type(supervisor['exit_code']) is int and supervisor['exit_code']==0
    assert type(result['oracle_tests']) is int and result['oracle_tests']==spec['oracle_tests']==15
    seconds=b.number(result['seconds'],180);whole=b.number(supervisor['seconds'],180)
    assert seconds<=whole
    for key in ('worker_seconds','computation_seconds','oracle_seconds'):b.number(result[key],seconds)
    assert b.number(result['normal_cleanup_seconds'],10)==b.number(supervisor['normal_cleanup_seconds'],10)
    assert result['normal_cleanup_seconds']<=whole
    assert [r['name'] for r in result['fixtures']]==[r['name'] for r in spec['inputs']['fixtures']]
    assert len(result['fixtures'])==2
    for row in result['fixtures']:
        assert all(row[key] is True for key in ('complete','independent_all257_agree','historical53_saved_fields_agree',
            'independent_owner_top_identities_agree','independent_base_paired_proofs_agree','all_forward_recurrences_checked'))
    for key in ('peak_rss_kib','supervisor_peak_rss_kib'):
        assert type(result[key]) is int and 0<result[key]<=spec['per_process_address_space_bytes']//1024


def build():
    b.require_checks()
    cp=b.LIT/'potential-tightening-v1/contract.json';ep=b.LIT/'potential-tightening-v1/evidence/results.json'
    parent=json.loads(cp.read_text());evidence=json.loads(ep.read_text())
    result=copy.deepcopy(parent)
    result.update(schema='gamma.owner-path-cap.contract.v1',active=False,
        parent53_contract={'path':str(cp.relative_to(b.LIT)),'sha256':b.sha(cp)},
        parent53_evidence={'path':str(ep.relative_to(b.LIT)),'sha256':b.sha(ep)},
        parent53_arms={a['cohort']:a for a in evidence['arms']},
        predictions={'P1':'required true: exact53 reconstruction, independent owner/schedule proof and all257 dominance',
                     'P2':'uncertain: some cohort/budget raw charge gain',
                     'P3':'uncertain: some cohort largest-positive-k increases',
                     'P4':'uncertain: some positive bound at k>=3; report per-cohort k3 prominently',
                     'P5':'uncertain: some positive unrestricted k256 bound'},
        pre_freeze_audit={'private_inputs_opened':False,'synthetic_only':True})
    b.accepted_parent53(result,parent,evidence)
    for p in (cp,ep):result['public_files'][str(p.relative_to(b.LIT))]=b.sha(p)
    fp=b.LIT/'support-budget-feasibility-v1/evidence/public-lineage.json'
    result['feasibility59']={'path':str(fp.relative_to(b.LIT)),'sha256':b.sha(fp)}
    result['public_files'][str(fp.relative_to(b.LIT))]=b.sha(fp)
    feasibility=json.loads(fp.read_text())
    result['public_files'].update(feasibility['public_files'])
    b.verify_parent50(result);b.verify_parent53(result);b.verify_feasibility(result)
    spec=json.loads((b.HERE/'synthetic-spec.json').read_text())
    measured=json.loads((b.HERE/'synthetic-results.json').read_text())
    supervisor=json.loads((b.HERE/'synthetic-supervisor.json').read_text())
    check_synthetic_receipts(spec,measured,supervisor,b.sha(b.HERE/'synthetic-spec.json'))
    # All inherited execution dependencies remain explicitly verified, including
    # the shared53 shape/receipt validator and invented fixture used by tests.
    code=dict(parent['code_hashes'])|spec['code_hashes']|result['public_files']
    for relative,h in code.items():assert b.sha(b.LIT/relative)==h,relative
    for p in b.HERE.iterdir():
        if p.suffix=='.py' or p.name in ('FREEZE.md','synthetic-spec.json','synthetic-results.json','synthetic-supervisor.json'):
            code[str(p.relative_to(b.LIT))]=b.sha(p)
    for p in ('potential-tightening-v1/report.py','potential-tightening-v1/test_report.py'):
        code[p]=b.sha(b.LIT/p)
    result['code_hashes']=code
    runtime=dict(parent['runtime_files'])|spec['runtime_hashes']
    for p,h in runtime.items():assert b.sha(p)==h,p
    result['runtime_files']=runtime
    assert spec['python_bin']==result['python_bin'] and len(result['private_files'])==9
    return result


def activate(current,pending):
    b.strict_equal(current,pending);assert pending['active'] is False
    for p,h in pending['code_hashes'].items():assert b.sha(b.LIT/p)==h
    for p,h in pending['runtime_files'].items():assert b.sha(p)==h
    result=copy.deepcopy(pending);result['active']=True
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--activate',action='store_true');args=parser.parse_args()
    current=build()
    if args.activate:
        value=activate(current,json.loads((b.HERE/'pending-contract.json').read_text()));path=b.HERE/'contract.json'
    else:value=current;path=b.HERE/'pending-contract.json'
    b.write(path,value);print(json.dumps({'path':str(path),'sha256':b.sha(path),'active':value['active'],'private_inputs_opened':False}))
