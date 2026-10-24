"""Item62 explicit tiny oracle, combining required slots and joint path caps.

Reuses mathematical item60/61 oracles, not production kernels or private data.
Enumerates all literal occurrences; no scalable corpus implementation claimed.
"""
import importlib.util
from pathlib import Path


def load(name,relative):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).resolve().parents[1]/relative)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

joint=load('required_joint62_parent60','joint-path-cap-v1/proof.py')
required=load('required_joint62_parent61','required-owner-cap-v1/proof.py')


def allocate(functions,forced,slots):
    """Exact finite required allocation with arbitrary nonnegative baselines."""
    if not __debug__:raise RuntimeError('normal assertions required')
    assert type(slots) is int and slots>=0
    assert type(forced) is list and forced==sorted(set(forced)) and set(forced)<=set(functions)
    for pid,values in functions.items():
        assert type(pid) is str and type(values) is list and values
        assert all(type(value) is int and value>=0 for value in values)
        increments=[b-a for a,b in zip(values,values[1:])]
        assert all(value>=0 for value in increments)
        assert increments==sorted(increments,reverse=True)
    r=len(forced)
    if slots<r:return None
    forced_set=set(forced);lower={pid:int(pid in forced_set) for pid in functions}
    assert all(lower[pid]<len(values) for pid,values in functions.items())
    assert slots<=sum(len(values)-1 for values in functions.values())
    zero_baseline=sum(values[0] for values in functions.values())
    baseline=sum(values[lower[pid]] for pid,values in functions.items())
    marginals=[]
    for pid,values in functions.items():
        for rank in range(lower[pid]+1,len(values)):
            marginals.append((values[rank]-values[rank-1],pid,rank))
    marginals.sort(key=lambda row:(-row[0],row[1],row[2]))
    chosen=[];allocation=dict(lower);total=baseline
    for value,pid,rank in marginals[:slots-r]:
        assert rank==allocation[pid]+1
        allocation[pid]=rank;chosen.append((pid,rank,value));total+=value
    assert sum(allocation.values())==slots
    return {'zero_baseline':zero_baseline,'mandatory_baseline':baseline,
        'mandatory_increment':baseline-zero_baseline,'charge':total,
        'residual_choices':chosen,'allocation':allocation}


def certificate(texts,banned,q,capacity=256,denominator=1):
    if not __debug__:raise RuntimeError('normal assertions required')
    base60=joint.certificate(texts,banned,q,capacity,denominator)
    base61=required.certificate(texts,banned,q,capacity,denominator)
    assert base60['L']==base61['base57']['L']
    assert base60['owner_prefixes']==base61['base57']['owner_prefixes']
    assert base60['shared_prefix']==base61['base57']['shared_prefix']
    forced=base61['forced_owners'];r=len(forced);splits=[]
    for j,owner_value in base61['required_owner_prefix'].items():
        s=capacity-j
        functions={pid:[min(base60['local_shared_prefixes'][pid][min(s,len(base60['local_shared_prefixes'][pid])-1)]+a,
                            base60['all_caps'][pid]) for a in values]
                   for pid,values in base60['owner_prefixes'].items()}
        allocation=allocate(functions,forced,j);assert allocation is not None
        prior61=owner_value+base60['shared_prefix'][min(s,len(base60['shared_prefix'])-1)]
        joint_charge=allocation['charge'];charge=min(joint_charge,prior61)
        assert joint_charge<=base60['alternatives'][j]['joint_charge']
        assert charge<=base60['alternatives'][j]['charge']
        splits.append({'one_owner_slots':j,'shared_slots':s,'joint_charge':joint_charge,
            'prior61_charge':prior61,'charge':charge,'owner_functions':functions,'allocation':allocation})
    rows=[]
    for k in range(capacity+1):
        if k<r:
            rows.append({'k':k,'empty_by_required_owners':True,'charge':None,'one_owner_slots':None,
                'numerator':None,'integer_lower_bound':None,'charge_reduction_vs60':None,'charge_reduction_vs61':None})
            continue
        selected=max((row for row in splits if row['one_owner_slots']<=k),key=lambda row:(row['charge'],-row['one_owner_slots']))
        charge=selected['charge'];numerator=base60['L']-charge
        assert charge<=base60['rows'][k]['charge'] and charge<=base61['rows'][k]['charge']
        rows.append({'k':k,'empty_by_required_owners':False,'charge':charge,
            'one_owner_slots':selected['one_owner_slots'],'numerator':numerator,
            'integer_lower_bound':-(-numerator//denominator),
            'charge_reduction_vs60':base60['rows'][k]['charge']-charge,
            'charge_reduction_vs61':base61['rows'][k]['charge']-charge})
    return {'base60':base60,'base61':base61,'forced_owners':forced,'coverage_floor':r,
        'split_rows':splits,'rows':rows}
