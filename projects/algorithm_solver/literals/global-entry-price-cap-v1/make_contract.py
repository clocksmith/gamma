"""Public-only inactive binding; no original path stat/open or measurement."""
import argparse
import copy
from pathlib import Path
import binding as b

FILES=('binding.py','production.py','integration.py','run.py','report.py','supervise.py','make_contract.py',
       'test_corpus_binding.py','test_corpus_integration.py','test_corpus_supervise.py',
       'DRAFT-CORPUS.md','FREEZE.md','synthetic-spec.json','synthetic-results.json',
       'synthetic-supervisor.json')
PURE_HELPERS=('owner-path-cap-v1/report.py','owner-path-cap-v1/test_report.py',
              'potential-tightening-v1/report.py','potential-tightening-v1/test_report.py',
              'support-coverage-floor-v1/coverage.py','support-coverage-floor-v1/report.py',
              'required-owner-cap-v1/allocation.py',
              'joint-path-cap-v1/contract.json')  # Public configuration fixture in the binding tests.


def merge_pins(*mappings):
    result={}
    for mapping in mappings:
        for path,h in mapping.items():
            assert path not in result or result[path]==h,('incompatible inherited pin',path)
            result[path]=h
    return result


def build():
    """Only explicit public metadata/code/runtime paths are accessed."""
    b.require_checks()
    cp=b.LIT/'owner-path-cap-v1/contract.json'
    ep=b.LIT/'owner-path-cap-v1/evidence/results.json'
    parent,evidence=b.read(cp),b.read(ep)
    result=copy.deepcopy(parent)
    result.update(schema='gamma.global-entry-price-cap.contract.v1',active=False,work=b.WORK,
        parent57_contract={'path':str(cp.relative_to(b.LIT)),'sha256':b.sha(cp)},
        parent57_evidence={'path':str(ep.relative_to(b.LIT)),'sha256':b.sha(ep)},
        parent57_arms={a['cohort']:a for a in evidence['arms']},
        carrier_limits=copy.deepcopy(b.CARRIER_LIMITS),
        lambda_family=[0]+[1000000*2**r for r in range(14)],
        price_diagnostics=copy.deepcopy(b.PRICE_DIAGNOSTICS),
        predictions={'P1':'required true: full original28/50/53/57 and66 reconstruction; fresh56/61; every recurrence and row; null below floor; domination61',
                     'P2':'uncertain: some cohort strict raw charge gain versus61 at k3',
                     'P3':'uncertain: some cohort largest-positive defined k increases versus61',
                     'P4':'uncertain: some cohort strict raw charge gain versus61 at k256',
                     'P5':'uncertain: some positive combined integer bound at k256'},
        price_range_scope='Fixed15 global-entry prices; no spanning/optimal-price claim or private adaptation.',
        headline_definition='min(T61(k),global_charge) for k>=fresh floor; null below floor; same q53,L,D,universe and capacity',
        pre_freeze_audit={'private_inputs_opened':False,'private_paths_statted':False,
                         'private_size_probe':False,'public_metadata_only':True})
    for path in (cp,ep):result['public_files'][str(path.relative_to(b.LIT))]=b.sha(path)
    for field,relative in (
        ('feasibility59','support-budget-feasibility-v1/evidence/public-lineage.json'),
        ('parent56_contract','support-coverage-floor-v1/contract.json'),
        ('parent56_evidence','support-coverage-floor-v1/evidence/results.json'),
        ('context61_contract','required-owner-cap-v1/contract.json'),
        ('context61_evidence','required-owner-cap-v1/evidence/results.json'),
        ('synthetic_spec','global-entry-price-cap-v1/synthetic-spec.json'),
        ('synthetic_result','global-entry-price-cap-v1/synthetic-results.json'),
        ('synthetic_supervisor','global-entry-price-cap-v1/synthetic-supervisor.json')):
        path=b.LIT/relative
        result[field]={'path':relative,'sha256':b.sha(path)}
        result['public_files'][relative]=b.sha(path)
    context=b.read(b.LIT/result['context61_evidence']['path'])
    result['context61_arms']={a['cohort']:a for a in context['arms']}
    coverage=b.read(b.LIT/result['parent56_evidence']['path'])
    result['parent56_arms']={a['cohort']:a for a in coverage['arms']}
    for name in ('owner-path-cap-v1','required-owner-cap-v1'):
        for file in ('production-supervisor.json','report-supervisor.json'):
            relative=name+'/evidence/'+file
            result['public_files'][relative]=b.sha(b.LIT/relative)
    for file in ('production-supervisor.json','supervisor.json'):
        relative='support-coverage-floor-v1/evidence/'+file
        result['public_files'][relative]=b.sha(b.LIT/relative)
    feasibility=b.read(b.LIT/result['feasibility59']['path'])
    result['public_files']=merge_pins(result['public_files'],feasibility['public_files'])
    spec=b.read(b.HERE/'synthetic-spec.json')
    measured=b.read(b.HERE/'synthetic-results.json')
    supervisor=b.read(b.HERE/'synthetic-supervisor.json')
    b.accepted_synthetic(spec,measured,supervisor,result['synthetic_spec']['sha256'])
    code=merge_pins(parent['code_hashes'],spec['code_hashes'],result['public_files'])
    for name in FILES:
        path=b.HERE/name;relative=str(path.relative_to(b.LIT))
        code=merge_pins(code,{relative:b.sha(path)})
    for relative in PURE_HELPERS:code=merge_pins(code,{relative:b.sha(b.LIT/relative)})
    result['code_hashes']=code
    result['runtime_files']=merge_pins(parent['runtime_files'],spec['runtime_hashes'])
    for relative,h in code.items():assert b.sha(b.LIT/relative)==h,relative
    for path,h in result['runtime_files'].items():assert b.sha(path)==h,path
    assert spec['python_bin']==result['python_bin'] and len(result['private_files'])==9
    b.accepted_parent57(result,parent,evidence)
    b.verify_parent50(result);b.verify_parent53(result);b.verify_parent57(result)
    b.verify_feasibility(result);b.verify_parent56(result);b.verify_context61(result);b.verify_synthetic(result)
    return result


def activate(current,pending):
    b.strict_equal(current,pending);assert pending['active'] is False
    for path,h in pending['code_hashes'].items():assert b.sha(b.LIT/path)==h,path
    for path,h in pending['runtime_files'].items():assert b.sha(path)==h,path
    result=copy.deepcopy(pending);result['active']=True
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--activate',action='store_true')
    args=parser.parse_args();current=build()
    if args.activate:
        value=activate(current,b.read(b.HERE/'pending-contract.json'));path=b.HERE/'contract.json'
    else:
        value=current;path=b.HERE/'pending-contract.json'
    b.write(path,value)
    print({'path':str(path),'sha256':b.sha(path),'active':value['active'],'private_inputs_opened':False})
