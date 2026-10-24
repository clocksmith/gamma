"""Pure required-owner priced allocation integration; no loader or search."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent


def module(name,component,file):
    spec=importlib.util.spec_from_file_location(name,HERE.parent/component/file)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj


priced=module('required68_priced63','entry-price-path-cap-v1','caps.py')
allocation=module('required68_allocation61','required-owner-cap-v1','allocation.py')
coverage=module('required68_coverage56','support-coverage-floor-v1','coverage.py')
coverage_report=module('required68_coverage_report56','support-coverage-floor-v1','report.py')
normalized=priced.normalized;digest=priced.digest
exact=coverage_report.exact;integer=coverage_report.integer


def scientific63(proof):
    return {'schema':proof['schema'],'base57':priced.scientific57(proof['base57']),
            **{key:proof[key] for key in priced.COMMON}}


def identity(proof,source_hashes,banned,capacity=256):
    integer(capacity,0);base=proof['base57'];tight=base['base']['tightened']
    assert type(source_hashes) is dict and set(source_hashes)==set(base['owner_caps'])
    for pid,h in source_hashes.items():
        assert type(pid) is str;coverage_report.hash_string(h)
    assert type(banned) in (set,list,tuple) and all(type(word) is str and word for word in banned)
    assert len(proof['rows'])==len(base['rows'])==capacity+1
    return {'source_identity_sha256':digest(source_hashes),'banned_set_sha256':digest(sorted(set(banned))),
        'priced63_scientific_sha256':digest(scientific63(proof)),
        'potential_sha256':base['base']['digests']['potentials_sha256'],
        'path_numerator':sum(tight['path_numerators'].values()),
        'denominator':integer(tight['denominator'],1),'capacity':capacity}


def combine(proof,baseline61,required,*,priced_identity,required_identity):
    if not __debug__:raise RuntimeError('normal assertions required')
    exact(priced_identity,required_identity)
    assert set(priced_identity)=={'source_identity_sha256','banned_set_sha256','priced63_scientific_sha256',
        'potential_sha256','path_numerator','denominator','capacity'}
    for key in ('source_identity_sha256','banned_set_sha256','priced63_scientific_sha256','potential_sha256'):
        coverage_report.hash_string(priced_identity[key])
    assert priced_identity['priced63_scientific_sha256']==digest(scientific63(proof))
    base=proof['base57'];tight=base['base']['tightened']
    assert priced_identity['potential_sha256']==base['base']['digests']['potentials_sha256']
    L=integer(priced_identity['path_numerator']);D=integer(priced_identity['denominator'],1)
    B=integer(priced_identity['capacity'],0)
    exact(L,sum(tight['path_numerators'].values()));exact(D,tight['denominator'])
    assert len(proof['rows'])==len(baseline61['rows'])==len(required['rows'])==B+1
    r=integer(required['coverage_floor'],0);exact(r,baseline61['coverage_floor'])
    old_fields={'k','empty_by_required_owners','one_owner_slots','shared_slots','charge','numerator','integer_lower_bound'}
    extra=('baseline61_charge','baseline63_charge','comparison_max_charge','comparison_max_integer_lower_bound',
           'charge_reduction_vs61','charge_reduction_vs63','charge_reduction_vsmax',
           'integer_bound_gain_vs61','integer_bound_gain_vs63','integer_bound_gain_vsmax')
    rows=[];previous=None
    for k,(row,a,b) in enumerate(zip(required['rows'],baseline61['rows'],proof['rows'])):
        assert set(row)==set(a)==old_fields
        exact(row['k'],k);exact(a['k'],k);exact(b['k'],k)
        exact(row['empty_by_required_owners'],k<r);exact(a['empty_by_required_owners'],k<r)
        if k<r:
            assert all(row[key] is None and a[key] is None for key in old_fields-{'k','empty_by_required_owners'})
            rows.append({**row,**dict.fromkeys(extra)});continue
        for value in (row,a,b):
            integer(value['charge'],0);integer(value['one_owner_slots'],0,k)
            integer(value['shared_slots'],0,B-value['one_owner_slots'])
            exact(value['numerator'],L-value['charge']);exact(value['integer_lower_bound'],-(-value['numerator']//D))
        assert row['one_owner_slots']>=r and a['one_owner_slots']>=r
        best=min(a['charge'],b['charge']);best_lower=-(-(L-best)//D)
        assert best_lower==max(a['integer_lower_bound'],b['integer_lower_bound'])
        assert row['charge']<=best
        assert previous is None or row['charge']>=previous;previous=row['charge']
        rows.append({**row,'baseline61_charge':a['charge'],'baseline63_charge':b['charge'],
            'comparison_max_charge':best,'comparison_max_integer_lower_bound':best_lower,
            'charge_reduction_vs61':a['charge']-row['charge'],'charge_reduction_vs63':b['charge']-row['charge'],
            'charge_reduction_vsmax':best-row['charge'],
            'integer_bound_gain_vs61':row['integer_lower_bound']-a['integer_lower_bound'],
            'integer_bound_gain_vs63':row['integer_lower_bound']-b['integer_lower_bound'],
            'integer_bound_gain_vsmax':row['integer_lower_bound']-best_lower})
    return rows


def priced_history(proof,c,cohort,direction):
    expected=c['parent63_arms'][cohort];base=proof['base57'];tight=base['base']['tightened']
    assert digest(scientific63(proof))==expected['scientific_proof_sha256']
    if direction=='price_prefix_schedule':assert digest(proof)==expected['production_proof_sha256']
    else:assert direction=='price_suffix_schedule'
    fields='digests' if direction=='price_prefix_schedule' else 'independent_digests'
    exact(proof['digests'],expected[fields])
    exact(proof['rows'],expected['rows']);exact(proof['deltas_vs57'],expected['deltas_vs57'])
    exact(base['rows'],expected['baseline57_rows']);exact(tight['denominator'],expected['denominator'])
    exact(sum(tight['path_numerators'].values()),expected['path_numerator'])
    assert digest(priced.scientific57(base))==expected['baseline57_scientific_sha256']
    exact(base['base']['digests'],expected['baseline53_paired_digests'])


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
    assert expected['parent_scientific_proof_sha256']==digest(priced.scientific57(base))
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
