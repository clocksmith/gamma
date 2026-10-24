"""Item68 tiny forced-owner/priced-prefix proof; no loader or scalable kernel.

The unchanged61/63 tiny proofs supply reachability, finite concave prefixes and
same-q baselines. Only the constrained use of the priced prefixes is new.
"""
import importlib.util
from pathlib import Path


def module(name,component):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).resolve().parents[1]/component/'proof.py')
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

required=module('required_price68_base61','required-owner-cap-v1')
priced=module('required_price68_base63','entry-price-path-cap-v1')


def certificate(texts,banned,q,lambdas,capacity=256,denominator=1):
    if not __debug__:raise RuntimeError('normal assertions required')
    assert type(texts) is dict and texts
    assert all(type(pid) is str and type(text) is str and text for pid,text in texts.items())
    assert not isinstance(banned,(str,bytes))
    banned=set(banned);assert all(type(word) is str and word for word in banned)
    #63 checks complete q edges, strict integer scalars and fixed supplied prices.
    price=priced.certificate(texts,banned,q,lambdas,capacity,denominator)
    old=required.certificate(texts,banned,q,capacity,denominator)
    assert old['base57']==price['base57'],'both baselines must use identical q/geometry'
    forced=old['forced_owners'];r=len(forced);f=price['priced_prefixes'];base=old['base57']
    totals,choices,mandatory=required.required_allocation(f,forced,capacity)
    shared=base['shared_prefix'];rows=[]
    for k in range(capacity+1):
        if k<r:
            rows.append({'k':k,'empty_by_required_owners':True,'one_owner_slots':None,'shared_slots':None,
                'charge':None,'numerator':None,'integer_lower_bound':None,'charge_reduction_vs61':None,
                'charge_reduction_vs63':None,'charge_reduction_vs_min61_63':None})
            continue
        charge,negative=max((total+shared[min(capacity-j,len(shared)-1)],-j) for j,total in totals.items() if j<=k)
        j=-negative;numerator=base['L']-charge
        assert charge<=old['rows'][k]['charge'] and charge<=price['rows'][k]['charge']
        rows.append({'k':k,'empty_by_required_owners':False,'one_owner_slots':j,
            'shared_slots':min(capacity-j,len(shared)-1),'charge':charge,'numerator':numerator,
            'integer_lower_bound':-(-numerator//denominator),
            'charge_reduction_vs61':old['rows'][k]['charge']-charge,
            'charge_reduction_vs63':price['rows'][k]['charge']-charge,
            'charge_reduction_vs_min61_63':min(old['rows'][k]['charge'],price['rows'][k]['charge'])-charge})
    return {'base61':old,'base63':price,'forced_owners':forced,'coverage_floor':r,
        'shared_reachability':old['shared_reachability'],'owner_entry_counts':old['owner_entry_counts'],
        'mandatory_value':mandatory,'required_priced_prefix':totals,'remaining_marginal_choices':choices,'rows':rows}
