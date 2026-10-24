"""Pure item66/61 integration and public history checks; no input loader.

Numerical combined rows here are production-only. The report recomputes them
independently. All source-dependent authorities are reconstructed by callers.
"""
import importlib.util
from pathlib import Path
import caps

HERE=Path(__file__).resolve().parent
normalized=caps.normalized
digest=caps.digest


def module(name,component,file):
    spec=importlib.util.spec_from_file_location(name,HERE.parent/component/file)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj


allocation=module('global66_required_allocation','required-owner-cap-v1','allocation.py')
coverage=module('global66_coverage','support-coverage-floor-v1','coverage.py')
coverage_report=module('global66_coverage_report','support-coverage-floor-v1','report.py')
exact=coverage_report.exact
integer=coverage_report.integer


def identity(global_proof,source_hashes,banned,capacity=256):
    """Bind combination to one complete same-q baseline and external geometry."""
    integer(capacity,0)
    base=global_proof['base57'];tight=base['base']['tightened']
    assert type(source_hashes) is dict and set(source_hashes)==set(base['owner_caps'])
    for pid,h in source_hashes.items():
        assert type(pid) is str;coverage_report.hash_string(h)
    assert type(banned) in (set,list,tuple) and all(type(word) is str and word for word in banned)
    D=integer(tight['denominator'],1);L=sum(tight['path_numerators'].values())
    integer(L)
    assert len(global_proof['rows'])==len(base['rows'])==capacity+1
    return {'source_identity_sha256':digest(source_hashes),'banned_set_sha256':digest(sorted(set(banned))),
            'base57_scientific_sha256':digest(caps.scientific57(base)),
            'potential_sha256':base['base']['digests']['potentials_sha256'],
            'path_numerator':L,'denominator':D,'capacity':capacity}


def combine(global_proof,required,*,global_identity,required_identity):
    """Explicit min(T61,G), never a fictitious allocation for a global winner."""
    if not __debug__:raise RuntimeError('normal assertions required')
    exact(global_identity,required_identity)
    assert set(global_identity)=={'source_identity_sha256','banned_set_sha256','base57_scientific_sha256',
        'potential_sha256','path_numerator','denominator','capacity'}
    for key in ('source_identity_sha256','banned_set_sha256','base57_scientific_sha256','potential_sha256'):
        coverage_report.hash_string(global_identity[key])
    base=global_proof['base57'];tight=base['base']['tightened']
    assert global_identity['base57_scientific_sha256']==digest(caps.scientific57(base))
    assert global_identity['potential_sha256']==base['base']['digests']['potentials_sha256']
    L=integer(global_identity['path_numerator']);D=integer(global_identity['denominator'],1)
    B=integer(global_identity['capacity'],0)
    exact(L,sum(tight['path_numerators'].values()));exact(D,tight['denominator'])
    assert len(global_proof['rows'])==len(base['rows'])==len(required['rows'])==B+1
    G=integer(global_proof['global_charge'],0);r=integer(required['coverage_floor'],0)
    prices=global_proof['price_rows'];winner=integer(global_proof['selected_price_index'],0,len(prices)-1)
    assert winner==min(range(len(prices)),key=lambda i:(prices[i]['charge'],prices[i]['lambda']))
    exact(G,prices[winner]['charge'])
    for price in prices:
        assert set(price)=={'lambda','entry_charge','residual_cap','charge','numerator','integer_lower_bound'}
        lam=integer(price['lambda'],0);res=integer(price['residual_cap'],0)
        exact(price['entry_charge'],lam*B);exact(price['charge'],lam*B+res)
        exact(price['numerator'],L-price['charge']);exact(price['integer_lower_bound'],-(-price['numerator']//D))
    fields=('baseline61_charge','global_charge','charge','numerator','integer_lower_bound',
            'charge_reduction_vs61','integer_bound_gain_vs61','active_bound')
    out=[];previous=None
    for k,(old,old57,kernel) in enumerate(zip(required['rows'],base['rows'],global_proof['rows'])):
        assert set(old)=={'k','empty_by_required_owners','one_owner_slots','shared_slots','charge','numerator','integer_lower_bound'}
        exact(old['k'],k);exact(old['empty_by_required_owners'],k<r)
        exact(kernel['k'],k);exact(kernel['charge'],min(old57['charge'],G))
        if k<r:
            assert all(old[key] is None for key in old if key not in ('k','empty_by_required_owners'))
            out.append({'k':k,'empty_by_required_owners':True,**dict.fromkeys(fields)})
            continue
        oldcharge=integer(old['charge'],0);integer(old['one_owner_slots'],r,k)
        integer(old['shared_slots'],0,B-old['one_owner_slots'])
        exact(old['numerator'],L-oldcharge);exact(old['integer_lower_bound'],-(-old['numerator']//D))
        assert oldcharge<=old57['charge']
        charge=min(oldcharge,G);num=L-charge;bound=-(-num//D)
        assert previous is None or charge>=previous;previous=charge
        out.append({'k':k,'empty_by_required_owners':False,'baseline61_charge':oldcharge,
            'global_charge':G,'charge':charge,'numerator':num,'integer_lower_bound':bound,
            'charge_reduction_vs61':oldcharge-charge,'integer_bound_gain_vs61':bound-old['integer_lower_bound'],
            'active_bound':'global' if G<oldcharge else 'required-owner' if oldcharge<G else 'tie'})
    return out


def coverage_history(proof,inputs,c,cohort,direction):
    expected=c['parent56_arms'][cohort]
    coverage_report.proof_shape(proof,c['parent50_arms'][cohort],set(inputs['texts']),direction)
    assert len(proof['owner_classes'])==len(inputs['pool'])
    for key in ('source_success','owner_classes','shared_entry_ids','forced_source_ids','private_character_source_ids'):
        assert digest(proof[key])==expected[key+'_sha256']
    exact(proof['occurrences'],expected['occurrences']);exact(proof['occurrence_sha256'],expected['occurrence_sha256'])
    exact(len(proof['forced_source_ids']),expected['coverage_floor']);exact(expected['coverage_floor'],3)
    exact(proof['private_character_entries'],expected['private_character_entries'])
    public='production_prefix_sha256' if direction=='prefix_reachable' else 'independent_suffix_sha256'
    assert digest(proof[direction])==expected[public]
    return proof['forced_source_ids']


def required_history(required,base,coverage,c,cohort,direction):
    """Reconcile scientific61 only; its original inherited-read metadata differs."""
    expected=c['context61_arms'][cohort];D=base['base']['tightened']['denominator']
    L=sum(base['base']['tightened']['path_numerators'].values())
    exact(expected['denominator'],D);exact(expected['path_numerator'],L)
    assert expected['parent_scientific_proof_sha256']==digest(caps.scientific57(base))
    for key,old in (('capped_prefixes','inherited_capped_prefixes_sha256'),
                    ('owner_caps','inherited_owner_caps_sha256'),('shared_prefix','inherited_shared_prefix_sha256')):
        assert digest(base[key])==expected[old]
    exact(required['coverage_floor'],len(coverage['forced_source_ids']));exact(required['coverage_floor'],expected['coverage_floor'])
    for key in ('forced_source_ids','source_success','owner_classes'):
        assert digest(coverage[key])==expected[key+'_sha256']
    exact(coverage['occurrences'],expected['coverage_occurrences']);exact(coverage['occurrence_sha256'],expected['coverage_occurrence_sha256'])
    public='production_prefix_sha256' if direction=='prefix_reachable' else 'independent_suffix_sha256'
    assert digest(coverage[direction])==expected[public]
    exact(required['mandatory_value'],expected['mandatory_value']);assert digest(required)==expected['allocation_sha256']
    for key in ('remaining_marginal_choices','final_owner_counts'):assert digest(required[key])==expected[key+'_sha256']
    exact(normalized(required['rows']),expected['rows']);exact(base['rows'],expected['baseline57_rows'])
    deltas=[{'k':row['k'],'empty_by_required_owners':row['empty_by_required_owners'],
        'charge_reduction':None if row['empty_by_required_owners'] else old['charge']-row['charge'],
        'integer_bound_gain':None if row['empty_by_required_owners'] else row['integer_lower_bound']-old['integer_lower_bound']}
        for row,old in zip(required['rows'],base['rows'])]
    exact(deltas,expected['deltas_vs57'])
