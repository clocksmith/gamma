"""Small exact cost diagnostics; finite enumerated optimum, not global optimality."""
from dataclasses import replace
from itertools import combinations, product
import math
import harness as h


def cost_or_failure(data,pieces,state):
    try:
        result=h.exact_measure(data,pieces,state)
        return {'eligible':True,'state_id':result['state_id'],'package_bits':result['package_bits'],
                'input_bits':result['input_bits'],'selections':result['selections'],'choices':state.choices,'piece_ids':state.piece_ids}
    except h.Ineligible as error:
        return {'eligible':False,'state_id':h.state_identity(state),'reason':str(error),'choices':state.choices,'piece_ids':state.piece_ids}


def support_and_reference(data,pieces,base,candidate_ids):
    h.validate_dataset(data)
    ids=tuple(sorted(candidate_ids))
    h.require(len(ids)<=3 and len(set(ids))==len(ids),'tiny reference supports at most three candidates')
    h.require(not (set(ids)&set(base.piece_ids)),'candidate already in base')
    h.require(all(key in pieces for key in ids),'unknown reference candidate')
    problems=[problem for problem,_ in base.choices]
    alternatives=[]
    base_choices=dict(base.choices)
    for problem in problems:
        target=data['variants'][base_choices[problem]]
        valid=[]
        for key,variant in sorted(data['variants'].items()):
            if variant['problem_id']!=problem or variant['language']!=target['language'] or variant['contract_sha256']!=target['contract_sha256']:continue
            try:h.qualification(data,variant)
            except h.Ineligible:continue
            valid.append(key)
        alternatives.append([(problem,key) for key in valid])
    h.require(all(alternatives) and 2**len(ids)*math.prod(map(len,alternatives))<=32,'tiny exhaustive state bound')
    baseline=cost_or_failure(data,pieces,base)
    records=[];by_subset={}
    for n in range(len(ids)+1):
        for subset in combinations(ids,n):
            for choices in product(*alternatives):
                state=replace(base,piece_ids=tuple(sorted(base.piece_ids+subset)),choices=tuple(choices))
                row=cost_or_failure(data,pieces,state);row['added']=subset
                records.append(row)
                if tuple(choices)==base.choices:by_subset[subset]=row
    eligible=[r for r in records if r['eligible']]
    best=min(eligible,key=lambda r:(r['package_bits'],r['input_bits'],r['state_id'])) if eligible else None
    fixed=[row for row in by_subset.values() if row['eligible']]
    fixed_best=min(fixed,key=lambda r:(r['package_bits'],r['input_bits'],r['state_id'])) if fixed else None
    support=[]
    for key in ids:
        text=pieces[key].text;occurrences={}
        for choices in alternatives:
            for _,variant_id in choices:
                source=data['variants'][variant_id]['source']
                found=[i for i in range(len(source)) if source.startswith(text,i)]
                if found:occurrences[variant_id]=found
        measure=by_subset[(key,)]
        support.append({'piece_id':key,'utf8_bytes':len(text.encode()),'occurrences_by_variant':occurrences,
                        'distinct_problem_coverage':len({data['variants'][k]['problem_id'] for k in occurrences}),
                        'exact_single_add':measure,
                        'package_bit_savings':baseline['package_bits']-measure['package_bits'] if baseline['eligible'] and measure['eligible'] else None})
    pairs=[]
    for a,b in combinations(ids,2):
        both=by_subset[(a,b)];one=by_subset[(a,)];two=by_subset[(b,)]
        all_valid=all(row['eligible'] for row in (baseline,one,two,both))
        overlap=[]
        for problem,key in base.choices:
            source=data['variants'][key]['source']
            pa=[i for i in range(len(source)) if source.startswith(pieces[a].text,i)]
            pb=[i for i in range(len(source)) if source.startswith(pieces[b].text,i)]
            if any(x<y+len(pieces[b].text) and y<x+len(pieces[a].text) for x in pa for y in pb):overlap.append(problem)
        pairs.append({'pieces':[a,b],'overlap_problem_ids':overlap,'exact_pair_add':both,
                      'pair_required_for_reachability':both['eligible'] and not one['eligible'] and not two['eligible'],
                      'package_savings_complementarity':one['package_bits']+two['package_bits']-baseline['package_bits']-both['package_bits'] if all_valid else None})
    # Reproducible dictionary-only greedy comparator on original source choices.
    selected=();current=by_subset[selected];trace=[]
    while current['eligible']:
        options=[by_subset[tuple(sorted(selected+(key,)))] for key in ids if key not in selected]
        options=[row for row in options if row['eligible'] and row['package_bits']<current['package_bits']]
        if not options:break
        chosen=min(options,key=lambda r:(r['package_bits'],r['input_bits'],r['state_id']))
        trace.append({'from':current['state_id'],'to':chosen['state_id'],'package_bit_gain':current['package_bits']-chosen['package_bits']})
        selected=tuple(chosen['added']);current=chosen
    return {'schema':'gamma.energy-tiny-reference.v1','evidence_class':data['evidence_class'],
            'candidate_ids':ids,'problem_ids':problems,'source_alternative_counts':list(map(len,alternatives)),
            'baseline':baseline,'support_matrix':support,'pair_complementarity':pairs,'enumerated_states':len(records),
            'records':records,'exhaustive_best':best,'dictionary_only_greedy':current,'greedy_trace':trace,
            'fixed_source_exhaustive_best':fixed_best,
            'dictionary_greedy_gap_bits':current['package_bits']-fixed_best['package_bits'] if current['eligible'] and fixed_best else None,
            'source_choice_opportunity_bits':fixed_best['package_bits']-best['package_bits'] if fixed_best and best else None,
            'greedy_gap_to_enumerated_joint_bits':current['package_bits']-best['package_bits'] if current['eligible'] and best else None,
            'semantic_dependencies_inferred':False,'candidate_execution':False,
            'limitations':['Only the enumerated <=3 candidate additions and <=32 source-choice states are exhausted.',
                           'Overlap and complementarity are exact encoding-cost properties, not semantic equivalence or dependency proofs.',
                           'Greedy is dictionary-only; the exhaustive comparator additionally enumerates the declared source alternatives.']}
