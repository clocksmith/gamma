"""Fresh global-price and required-owner replay; original nine inputs only after accepted production."""
import signal
import time
class HardDeadline(BaseException):pass
def _expired(*_):raise HardDeadline('independent report deadline')
BOOT_STARTED=time.monotonic() if __name__=='__main__' else None
if BOOT_STARTED is not None:
    signal.signal(signal.SIGALRM,_expired);signal.setitimer(signal.ITIMER_REAL,600)
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import binding as b
HERE=b.HERE;COHORTS=('R','naming');WORKER_SECONDS=600;PHASE_SECONDS=1200;ADDRESS_SPACE_BYTES=8*1024**3

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
prior=module('global66_report57',HERE.parent/'owner-path-cap-v1/report.py')
exact=prior.exact;shaped=prior.shaped;digest=prior.digest;integer=prior.integer;number=prior.number
sha=b.sha;write=b.write;config_limits=prior.config_limits
allocation=module('global66_required61',HERE.parent/'required-owner-cap-v1/allocation.py')

def read(path):
    path=Path(path).absolute()
    assert path.resolve()==path and path.is_file(),'direct retained carrier required'
    return b.read(path)

COMMON=('lambda_family','shared_counts','count_streams','price_caps','unpriced_caps','price_rows',
        'selected_price_index','global_charge','rows','deltas_vs57')
PROD_WORK=('baseline57_reconstructions','additional53_contexts','shared_structural_utility63','structural_groups',
 'terminal_positions_checked','shared_catalogue_entries','ancestor_group_visits','candidate_depths','allowed_endpoints',
 'banned_endpoints','owner_endpoints','shared_endpoints','multiplicity_cache_entries','multiplicity_divisions',
 'q_evaluations','price_residual_evaluations','forward_arc_candidates','forward_skip_candidates',
 'unpriced_arc_candidates','unpriced_skip_candidates','count_stream_records')
AUDIT_WORK=('baseline57_reconstructions','additional_old_contexts','old_occurrences_replayed','old_bellman_edges_checked',
 'support_suffix_positions_checked','support_groups_classified','shared_catalogue_entries','shared_catalogue_ac_occurrences',
 'shared_catalogue_trie_nodes','shared_trie_transitions','shared_terminal_hits','old_occurrences_reclassified',
 'old_owned_occurrence_counts_checked','banned_occurrences_matched','z_input_symbols','z_character_comparisons',
 'z_histogram_cells','endpoints_inspected','banned_endpoints_skipped','shared_occurrences','one_owner_occurrences',
 'count_records','q_evaluations','price_residual_evaluations','multiplicity_divisions','backward_candidates',
 'production_forward_candidates','production_forward_positions_checked','unpriced_backward_candidates',
 'unpriced_production_forward_candidates','unpriced_production_forward_positions_checked')
SHARED=('Original parser/source authority, item33 Index/verifier and unchanged50/53/57 baseline machinery. '
 'Global counts use independent AC shared totals and Z owner counts; backward schedules audit every forward recurrence. '
 'Fresh56 coverage uses trie/AC with every Boolean recurrence;61 allocation uses heap versus independent sort.')


def global_scientific(proof):
    return {'schema':proof['schema'],'base57':prior.scientific(proof['base57']),**{k:proof[k] for k in COMMON}}


def scientific(proof):
    return {'global':global_scientific(proof['global']),
        'coverage':{k:proof['coverage'][k] for k in b.coverage_report().COMMON_FIELDS},
        'required':proof['required'],'rows':proof['rows']}


def global_shape(proof,geometry,direction):
    """Public-checkable algebra only; independent source replay remains mandatory."""
    assert direction in ('price_prefix_schedule','price_suffix_schedule')
    isprod=direction=='price_prefix_schedule';unpriced='unpriced_prefix_schedule' if isprod else 'unpriced_suffix_schedule'
    extras=set() if isprod else {'production_forward_schedule_checked','production_forward_schedule_sha256',
        'production_unpriced_forward_checked','production_unpriced_forward_sha256','shared_dependency','scalar_replay'}
    assert set(proof)=={'schema','base57','digests','work',direction,unpriced,*COMMON}|extras
    assert proof['schema']=='gamma.global-entry-price-cap.supplied.v1'
    base=proof['base57'];tight=base['base']['tightened'];ids=set(base['owner_caps'])
    if isprod:prior.owner_shape(base,geometry)
    D=integer(tight['denominator'],1);L=sum(tight['path_numerators'].values())
    prices=[0]+[D*2**r for r in range(14)];exact(proof['lambda_family'],prices);K=15
    positions=endpoints=arcs=0
    for key in ('count_streams','price_caps','unpriced_caps',direction,unpriced):assert set(proof[key])==ids
    for pid in sorted(ids):
        caps=proof['price_caps'][pid];vectors=proof[direction][pid]
        assert type(caps) is list and len(caps)==K and type(vectors) is list and len(vectors)==K
        for cap in caps:integer(cap,0)
        assert caps==sorted(caps,reverse=True)
        n=len(vectors[0])-1;assert n>0;positions+=n;endpoints+=n*(n+1)//2
        for cap,vec in zip(caps,vectors):
            assert type(vec) is list and len(vec)==n+1
            for value in vec:integer(value,0)
            assert vec[0 if isprod else -1]==0 and vec[-1 if isprod else 0]==cap
            assert vec==sorted(vec,reverse=not isprod)
        exact(vectors[0],proof[unpriced][pid]);exact(caps[0],proof['unpriced_caps'][pid])
        # All-entry schedules contain every owner-only interval.
        assert caps[0]>=base['owner_caps'][pid]
        streams=proof['count_streams'][pid];assert type(streams) is list and len(streams)==n
        for start,stream in enumerate(streams):
            assert set(stream)=={'arcs','sha256'}
            arcs+=integer(stream['arcs'],0,n-start);prior.hash_string(stream['sha256'])
            if stream['arcs']==0:assert stream['sha256']==hashlib.sha256(b'').hexdigest()
    assert positions==geometry['source_characters']
    assert arcs+geometry['exact_ban_occurrences']==endpoints
    shared=proof['shared_counts'];assert type(shared) is list
    assert len(shared)==tight['class_counts']['2']
    shared_ids=[];shared_arcs=0
    for pair in shared:
        assert type(pair) is list and len(pair)==2
        shared_ids.append(integer(pair[0],0));shared_arcs+=integer(pair[1],2)
    assert shared_ids==sorted(set(shared_ids)) and shared_arcs<=arcs
    price_rows=[]
    for index,price in enumerate(prices):
        residual=sum(values[index] for values in proof['price_caps'].values());charge=price*256+residual;num=L-charge
        price_rows.append({'lambda':price,'entry_charge':price*256,'residual_cap':residual,'charge':charge,
            'numerator':num,'integer_lower_bound':-(-num//D)})
    exact(proof['price_rows'],price_rows)
    selected=min(range(K),key=lambda i:(price_rows[i]['charge'],i));G=price_rows[selected]['charge']
    exact(proof['selected_price_index'],selected);exact(proof['global_charge'],G)
    assert type(proof['rows']) is list and type(proof['deltas_vs57']) is list
    assert len(proof['rows'])==len(proof['deltas_vs57'])==257
    for k,(row,old,delta) in enumerate(zip(proof['rows'],base['rows'],proof['deltas_vs57'])):
        charge=min(G,old['charge']);num=L-charge;lower=-(-num//D)
        exact(row,{'k':k,'charge':charge,'baseline57_charge':old['charge'],'global_charge':G,'numerator':num,
            'integer_lower_bound':lower,'charge_reduction_vs57':old['charge']-charge})
        exact(delta,{'k':k,'charge_reduction':old['charge']-charge,'integer_bound_gain':lower-old['integer_lower_bound']})
    assert set(proof['digests'])=={k+'_sha256' for k in (*COMMON,direction,unpriced)}|{'base57_sha256'}
    for key in (*COMMON,direction,unpriced):assert proof['digests'][key+'_sha256']==digest(proof[key])
    assert proof['digests']['base57_sha256']==digest(prior.scientific(base))
    w=proof['work'];assert set(w)==set(PROD_WORK if isprod else AUDIT_WORK)
    for value in w.values():integer(value,0)
    assert w['baseline57_reconstructions']==1 and w['q_evaluations']==arcs
    assert w['price_residual_evaluations']==K*arcs and w['shared_catalogue_entries']==len(shared)
    if isprod:
        assert w['additional53_contexts']==w['shared_structural_utility63']==1
        assert w['structural_groups']==geometry['full_groups'] and w['terminal_positions_checked']==positions
        assert w['candidate_depths']==endpoints and w['ancestor_group_visits']<=endpoints
        assert w['allowed_endpoints']==w['count_stream_records']==arcs
        assert w['banned_endpoints']==geometry['exact_ban_occurrences']
        assert w['owner_endpoints']==arcs-shared_arcs==base['work']['schedule_one_owner_occurrences']
        assert w['shared_endpoints']==shared_arcs
        assert w['multiplicity_cache_entries']<=geometry['full_groups']
        assert w['multiplicity_divisions']==K*w['multiplicity_cache_entries']
        assert w['forward_arc_candidates']==K*arcs and w['forward_skip_candidates']==K*positions
        assert w['unpriced_arc_candidates']==arcs and w['unpriced_skip_candidates']==positions
    else:
        assert w['additional_old_contexts']==1
        assert w['old_occurrences_replayed']==w['old_bellman_edges_checked']==w['old_occurrences_reclassified']==tight['old_occurrences']
        assert w['support_suffix_positions_checked']==positions and w['support_groups_classified']==geometry['full_groups']
        assert w['endpoints_inspected']==endpoints
        assert w['banned_occurrences_matched']==w['banned_endpoints_skipped']==geometry['exact_ban_occurrences']
        assert w['shared_occurrences']==w['shared_catalogue_ac_occurrences']==w['shared_terminal_hits']==shared_arcs
        assert w['one_owner_occurrences']==arcs-shared_arcs==base['work']['schedule_occurrences_admitted']
        assert w['count_records']==arcs and w['multiplicity_divisions']==K*arcs
        assert w['backward_candidates']==w['production_forward_candidates']==K*arcs
        assert w['production_forward_positions_checked']==K*positions
        assert w['unpriced_backward_candidates']==w['unpriced_production_forward_candidates']==arcs
        assert w['unpriced_production_forward_positions_checked']==positions
        assert proof['production_forward_schedule_checked'] is proof['production_unpriced_forward_checked'] is True
        prior.hash_string(proof['production_forward_schedule_sha256']);prior.hash_string(proof['production_unpriced_forward_sha256'])
        assert type(proof['shared_dependency']) is type(proof['scalar_replay']) is str


def combined_rows(global_proof,required):
    """Independent minimum, with no production integration helper dependency."""
    base=global_proof['base57']['base']['tightened'];L=sum(base['path_numerators'].values());D=base['denominator']
    G=global_proof['global_charge'];r=required['coverage_floor'];rows=[]
    fields=('baseline61_charge','global_charge','charge','numerator','integer_lower_bound',
            'charge_reduction_vs61','integer_bound_gain_vs61','active_bound')
    for k,old in enumerate(required['rows']):
        row={'k':k,'empty_by_required_owners':k<r}
        if k<r:row.update(dict.fromkeys(fields))
        else:
            charge=min(old['charge'],G);num=L-charge;lower,remainder=divmod(num,D);lower+=int(remainder!=0)
            label='tie' if old['charge']==G else ('global' if G<old['charge'] else 'required-owner')
            row.update(baseline61_charge=old['charge'],global_charge=G,charge=charge,numerator=num,integer_lower_bound=lower,
                charge_reduction_vs61=old['charge']-charge,integer_bound_gain_vs61=lower-old['integer_lower_bound'],active_bound=label)
        rows.append(row)
    return rows


def shape(proof,geometry,direction='price_prefix_schedule'):
    assert set(proof)=={'global','coverage','required','rows','digests'}
    g=proof['global'];global_shape(g,geometry,direction);base=g['base57'];tight=base['base']['tightened']
    cov=proof['coverage'];covdir='prefix_reachable' if direction=='price_prefix_schedule' else 'suffix_reachable'
    expected={'old_pool_entries':len(cov['owner_classes']),'class_counts':tight['class_counts'],
        'old_occurrences':tight['old_occurrences'],'old_occurrence_order_sha256':tight['occurrence_sha256'],'geometry':geometry}
    b.coverage_report().proof_shape(cov,expected,set(base['owner_caps']),covdir)
    exact(cov['shared_entry_ids'],[row[0] for row in g['shared_counts']])
    # Even before source reads, independently redo every constrained allocation.
    required=shaped(allocation.independent(base['capped_prefixes'],base['shared_prefix'],cov['forced_source_ids'],
        sum(tight['path_numerators'].values()),tight['denominator']))
    exact(proof['required'],required);exact(proof['rows'],combined_rows(g,required))
    assert set(proof['digests'])=={key+'_sha256' for key in ('global','coverage','required','rows')}
    for key in ('global','coverage','required','rows'):assert proof['digests'][key+'_sha256']==digest(proof[key])


def historical_required(proof,c,cohort):
    """Match scientific commitments, not the predecessor's private read receipts."""
    g=proof['global'];base=g['base57'];cov=proof['coverage'];req=proof['required'];old=c['context61_arms'][cohort]
    old56=c['parent56_arms'][cohort];covdir='prefix_reachable' if 'prefix_reachable' in cov else 'suffix_reachable'
    b.coverage_report().proof_shape(cov,c['parent50_arms'][cohort],set(map(str,c['fit_ids'])),covdir)
    for key,public in (('source_success','source_success_sha256'),('owner_classes','owner_classes_sha256'),
        ('shared_entry_ids','shared_entry_ids_sha256'),('forced_source_ids','forced_source_ids_sha256'),
        ('private_character_source_ids','private_character_source_ids_sha256')):assert digest(cov[key])==old56[public]
    exact(cov['occurrences'],old56['occurrences']);assert cov['occurrence_sha256']==old56['occurrence_sha256']
    exact(cov['private_character_entries'],old56['private_character_entries'])
    assert digest(cov[covdir])==old56['production_prefix_sha256' if covdir=='prefix_reachable' else 'independent_suffix_sha256']
    exact(req['coverage_floor'],old56['coverage_floor']);exact(req['coverage_floor'],3)
    assert old['parent_scientific_proof_sha256']==digest(prior.scientific(base))
    assert old['source_identity_sha256']==c['parent57_arms'][cohort]['source_identity_sha256']
    assert old['banned_set_sha256']==c['parent57_arms'][cohort]['banned_set_sha256']
    for key in ('source_success','owner_classes','forced_source_ids'):assert digest(cov[key])==old[key+'_sha256']
    assert digest(cov[covdir])==old['production_prefix_sha256' if covdir=='prefix_reachable' else 'independent_suffix_sha256']
    for key in ('capped_prefixes','owner_caps','shared_prefix'):assert digest(base[key])==old['inherited_'+key+'_sha256']
    exact(cov['occurrences'],old['coverage_occurrences']);assert cov['occurrence_sha256']==old['coverage_occurrence_sha256']
    exact(req['coverage_floor'],old['coverage_floor']);exact(req['mandatory_value'],old['mandatory_value'])
    exact(req['rows'],old['rows']);exact(base['rows'],old['baseline57_rows'])
    deltas=[{'k':row['k'],'empty_by_required_owners':row['empty_by_required_owners'],
        'charge_reduction':None if row['empty_by_required_owners'] else before['charge']-row['charge'],
        'integer_bound_gain':None if row['empty_by_required_owners'] else row['integer_lower_bound']-before['integer_lower_bound']}
        for row,before in zip(req['rows'],base['rows'])]
    exact(deltas,old['deltas_vs57'])
    assert digest(req)==old['allocation_sha256']
    for key in ('remaining_marginal_choices','final_owner_counts'):assert digest(req[key])==old[key+'_sha256']
    tight=base['base']['tightened'];exact(tight['denominator'],old['denominator'])
    exact(sum(tight['path_numerators'].values()),old['path_numerator'])


def diagnostics(proof):
    g=proof['global'];prices=g['price_rows'];G=g['global_charge'];indices=[i for i,row in enumerate(prices) if row['charge']==G]
    active={'global':0,'required-owner':0,'tie':0}
    for row in proof['rows']:
        if not row['empty_by_required_owners']:active[row['active_bound']]+=1
    denominator=sum(active.values());i=indices[0];chosen=prices[i]
    return {'selected_price_index':i,'selected_category':'zero' if i==0 else ('maximum' if i==14 else 'interior'),
        'minimizing_indices':indices,'minimizer_count':len(indices),'tied':len(indices)>1,
        'charge_reduction_vs_lambda0':prices[0]['charge']-G,
        'integer_bound_gain_vs_lambda0':chosen['integer_lower_bound']-prices[0]['integer_lower_bound'],
        'defined_budget_denominator':denominator,'active_bound_counts':active,
        'active_bound_shares':{key:value/denominator if denominator else None for key,value in active.items()}}


def accepted_production(run,c,contract):
    config_limits(c);b.verify_parent50(c);b.verify_parent53(c);b.verify_parent57(c);b.verify_feasibility(c)
    b.verify_parent56(c);b.verify_context61(c)
    run=Path(run);assert not (run/'failure.json').exists();result,sup=read(run/'results.json'),read(run/'supervisor.json')
    assert set(result)=={'complete','validation_loaded','contract_sha256','seconds','arms'}
    assert set(sup)=={'complete','phase','contract_sha256','elapsed','cleanup_seconds','returncodes'}
    assert result['complete'] is sup['complete'] is True and result['validation_loaded'] is False
    assert sup['phase']=='production' and result['contract_sha256']==sup['contract_sha256']==contract
    exact(sup['returncodes'],[0,0]);number(sup['elapsed'],1200);number(sup['cleanup_seconds'],10);number(result['seconds'],sup['elapsed'])
    assert [a['cohort'] for a in result['arms']]==list(COHORTS)
    for raw in result['arms']:
        cohort=raw['cohort'];assert not (run/cohort/'failure.json').exists() and not (run/(cohort+'-failure.json')).exists()
        assert set(raw)=={'schema','cohort','complete','validation_loaded','contract_sha256','bindings','full_shape','proof','phase_seconds','seconds','peak_rss_kib'}
        assert raw['schema']=='gamma.global-entry-price-cap.arm.v1' and raw['complete'] is True and raw['validation_loaded'] is False
        assert raw['contract_sha256']==contract;number(raw['seconds'],min(600,result['seconds']));integer(raw['peak_rss_kib'],1,ADDRESS_SPACE_BYTES//1024)
        assert set(raw['phase_seconds'])=={'input','proof'}
        for value in raw['phase_seconds'].values():number(value,raw['seconds'])
        assert sum(raw['phase_seconds'].values())<=raw['seconds']
        exact(raw['full_shape'],c['full_shape'][cohort]);shape(raw['proof'],raw['full_shape']);historical_required(raw['proof'],c,cohort)
        base=raw['proof']['global']['base57'];assert set(base['owner_caps'])==set(map(str,c['fit_ids']))
        assert digest(raw['bindings'])==c['parent50_arms'][cohort]['bindings_sha256']
        assert raw['bindings']['source_hashes_sha256']==c['parent57_arms'][cohort]['source_identity_sha256']
        assert raw['bindings']['bans_sha256']==c['parent57_arms'][cohort]['banned_set_sha256']
        assert digest(prior.scientific(base))==c['parent57_arms'][cohort]['scientific_proof_sha256']
        assert digest(base)==c['parent57_arms'][cohort]['production_proof_sha256']
        exact(raw,read(run/cohort/'results.json'))
    return result,sup


def paired_shape(production,checked,geometry):
    shape(checked,geometry,'price_suffix_schedule');exact(scientific(production),scientific(checked))
    p=production['global'];v=checked['global'];prior.independent_shape(p['base57'],v['base57'],geometry)
    assert v['production_forward_schedule_sha256']==digest(p['price_prefix_schedule'])
    assert v['production_unpriced_forward_sha256']==digest(p['unpriced_prefix_schedule'])


def replay(cohort,inputs,raw,checker,c):
    exact(raw['bindings'],shaped(inputs['bindings']));exact(raw['full_shape'],inputs['geometry'])
    p=raw['proof'];g=p['global'];shape(p,raw['full_shape'])
    checked_global=shaped(checker.check(inputs['texts'],inputs['banned'],inputs['pool'],inputs['q'],inputs['seed'],inputs['alphabet'],inputs['denominator'],
        expected_source_hashes=inputs['source_hashes'],expected_old_banned=inputs['banned'],expected_old_certificate=inputs['parent_certificate'],
        expected_occurrence_sha256=c['parent50_arms'][cohort]['old_occurrence_order_sha256'],
        expected_base57_prefix_schedule=g['base57']['owner_prefix_schedule'],expected_price_prefix_schedule=g['price_prefix_schedule'],
        expected_unpriced_prefix_schedule=g['unpriced_prefix_schedule'],expected_count_streams=g['count_streams'],
        expected_price_caps=g['price_caps'],expected_shared_counts=g['shared_counts'],expected_price_rows=g['price_rows']))
    assert len(inputs['alphabet'])==len(set(inputs['alphabet']))==96 and all(len(s)==1 for s in inputs['alphabet'])
    assert set(inputs['alphabet'])<=set(inputs['pool']) and not set(inputs['pool'])&set(inputs['banned'])
    cov=shaped(b.coverage().replay(inputs['texts'],inputs['pool'],inputs['banned']))
    for key in b.coverage_report().COMMON_FIELDS:exact(p['coverage'][key],cov[key])
    b.coverage_report().check_vectors(inputs['texts'],inputs['pool'],p['coverage'],cov)
    base=checked_global['base57'];tight=base['base']['tightened']
    req=shaped(allocation.independent(base['capped_prefixes'],base['shared_prefix'],cov['forced_source_ids'],
        sum(tight['path_numerators'].values()),tight['denominator']))
    checked={'global':checked_global,'coverage':cov,'required':req,'rows':combined_rows(checked_global,req)}
    checked['digests']={key+'_sha256':digest(value) for key,value in checked.items()}
    paired_shape(p,checked,raw['full_shape']);historical_required(checked,c,cohort);exact(diagnostics(p),diagnostics(checked))
    fake={**raw,'proof':g['base57']}
    prior.compare53(fake,inputs,base,raw['full_shape'],c['parent53_arms'][cohort])
    basepublic=prior.prior.sanitize(cohort,inputs,{**raw,'proof':g['base57']['base']},base['base'],raw['full_shape'])
    prior.prior.compare50(cohort,basepublic,base['base']['lifted'],c['parent50_arms'][cohort])
    historical=c['parent57_arms'][cohort]
    assert digest(prior.scientific(base))==historical['scientific_proof_sha256']
    assert digest(g['base57'])==historical['production_proof_sha256']
    assert digest(base['owner_suffix_schedule'])==historical['independent_suffix_schedule_sha256']
    for key in ('rows','deltas_vs53'):exact(base[key],historical[key])
    return checked


def positive(rows):
    return max((r['k'] for r in rows if r['integer_lower_bound'] is not None and r['integer_lower_bound']>0),default=None)


def summary(cohort,raw,checked,c):
    p=raw['proof'];g=p['global'];base=g['base57'];tight=base['base']['tightened'];rows=p['rows'];cov=checked['coverage'];req=checked['required']
    r=req['coverage_floor'];G=g['price_rows'][g['selected_price_index']]
    deltas57=[{'k':row['k'],'charge_reduction':None if row['empty_by_required_owners'] else old['charge']-row['charge'],
        'integer_bound_gain':None if row['empty_by_required_owners'] else row['integer_lower_bound']-old['integer_lower_bound']}
        for row,old in zip(rows,base['rows'])]
    return {'schema':'gamma.global-entry-price-cap.report-arm.v1','cohort':cohort,'complete':True,'validation_loaded':False,
        'contract_sha256':raw['contract_sha256'],'parent57_evidence_sha256':c['parent57_evidence']['sha256'],
        'parent56_evidence_sha256':c['parent56_evidence']['sha256'],'context61_evidence_sha256':c['context61_evidence']['sha256'],
        'source_identity_sha256':raw['bindings']['source_hashes_sha256'],'banned_set_sha256':raw['bindings']['bans_sha256'],
        'bindings_sha256':digest(raw['bindings']),'parent_certificate_sha256':c['parent57_arms'][cohort]['parent_certificate_sha256'],
        'geometry':raw['full_shape'],'class_counts':tight['class_counts'],'denominator':tight['denominator'],
        'path_numerator':sum(tight['path_numerators'].values()),'old_occurrences':tight['old_occurrences'],
        'baseline57_scientific_sha256':digest(prior.scientific(base)),'baseline53_paired_digests':base['base']['digests'],
        'production_proof_sha256':digest(p),'scientific_proof_sha256':digest(scientific(checked)),
        'digests':p['digests'],'independent_digests':checked['digests'],
        'global_digests':g['digests'],'independent_global_digests':checked['global']['digests'],
        'rows':rows,'baseline61_rows':req['rows'],'baseline57_rows':base['rows'],'kernel66_min57_rows':g['rows'],'deltas_vs57':deltas57,
        'k3':rows[3],'k256':rows[256],'largest_positive_k':positive(rows),
        'baseline61_largest_positive_k':positive(req['rows']),'baseline57_largest_positive_k':positive(base['rows']),
        'strict_charge_budgets':sum(row['charge_reduction_vs61'] is not None and row['charge_reduction_vs61']>0 for row in rows),
        'strict_integer_budgets':sum(row['integer_bound_gain_vs61'] is not None and row['integer_bound_gain_vs61']>0 for row in rows),
        'coverage_floor':r,'empty_budgets':[row['k'] for row in rows if row['empty_by_required_owners']],
        'minimum_feasible_one_owner_budget':3,'forced_source_ids_sha256':digest(cov['forced_source_ids']),
        'coverage_occurrences':cov['occurrences'],'coverage_occurrence_sha256':cov['occurrence_sha256'],
        'production_coverage_prefix_sha256':digest(p['coverage']['prefix_reachable']),
        'independent_coverage_suffix_sha256':digest(cov['suffix_reachable']),
        'required_allocation_sha256':digest(req),'mandatory_value':req['mandatory_value'],
        'lambda_family':g['lambda_family'],'price_rows':g['price_rows'],'standalone_global':G,'price_diagnostics':diagnostics(checked),
        'production_work':g['work'],'report_work':checked['global']['work'],'baseline57_production_work':base['work'],
        'baseline57_report_work':checked['global']['base57']['work'],'baseline53_production_work':base['base']['work'],
        'baseline53_report_work':checked['global']['base57']['base']['work'],
        'fresh_coverage_work':{'source_positions':raw['full_shape']['source_characters'],'occurrences_per_direction':cov['occurrences'],
            'additional_recurrence_AC_pass':True,'forced_owners':r},
        'fresh_allocation_work':{'finite_marginals':sum(len(v)-1 for v in base['capped_prefixes'].values()),
            'residual_marginals':sum(len(v)-1 for v in base['capped_prefixes'].values())-r},
        'production_seconds':raw['seconds'],'production_peak_rss_kib':raw['peak_rss_kib'],
        'production_phase_seconds_sha256':digest(raw['phase_seconds']),
        'all257_independently_replayed':True,'all_global_price_forward_recurrences_checked':True,
        'all_unpriced_forward_recurrences_checked':True,'all57_forward_recurrences_checked':True,
        'all_coverage_recurrences_checked':True,'historical57_reconstructed':True,'fresh_original_proof_replay':True,
        'fresh_forced_owner_replay':True,'fresh_constrained_allocation_replay':True,
        'parent61_inherited57_authority':True,'shared_dependencies':SHARED}


ARM_FIELDS=set(('schema cohort complete validation_loaded contract_sha256 parent57_evidence_sha256 parent56_evidence_sha256 '
 'context61_evidence_sha256 source_identity_sha256 banned_set_sha256 bindings_sha256 parent_certificate_sha256 geometry class_counts '
 'denominator path_numerator old_occurrences baseline57_scientific_sha256 baseline53_paired_digests production_proof_sha256 '
 'scientific_proof_sha256 digests independent_digests global_digests independent_global_digests rows baseline61_rows baseline57_rows '
 'kernel66_min57_rows deltas_vs57 k3 k256 largest_positive_k baseline61_largest_positive_k baseline57_largest_positive_k '
 'strict_charge_budgets strict_integer_budgets coverage_floor empty_budgets minimum_feasible_one_owner_budget forced_source_ids_sha256 '
 'coverage_occurrences coverage_occurrence_sha256 production_coverage_prefix_sha256 independent_coverage_suffix_sha256 '
 'required_allocation_sha256 mandatory_value lambda_family price_rows standalone_global price_diagnostics production_work report_work '
 'baseline57_production_work baseline57_report_work baseline53_production_work baseline53_report_work fresh_coverage_work fresh_allocation_work '
 'production_seconds production_peak_rss_kib production_phase_seconds_sha256 all257_independently_replayed '
 'all_global_price_forward_recurrences_checked all_unpriced_forward_recurrences_checked all57_forward_recurrences_checked '
 'all_coverage_recurrences_checked historical57_reconstructed fresh_original_proof_replay fresh_forced_owner_replay '
 'fresh_constrained_allocation_replay parent61_inherited57_authority shared_dependencies independent_receipt_sha256 '
 'production_arm_sha256 production_results_sha256 production_supervisor_sha256 report_worker_seconds report_peak_rss_kib').split())


def combine(run,output,c,elapsed,returncodes):
    number(elapsed,1200);exact(returncodes,[0,0]);run,output=Path(run),Path(output)
    assert not (output/'failure.json').exists();contract=sha(HERE/'contract.json');production,sup=accepted_production(run,c,contract);arms=[]
    for cohort,raw in zip(COHORTS,production['arms']):
        assert not (output/(cohort+'-failure.json')).exists()
        checked=read(output/(cohort+'-proof.json'));a=read(output/(cohort+'.json'));assert set(a)==ARM_FIELDS
        paired_shape(raw['proof'],checked,raw['full_shape']);historical_required(checked,c,cohort)
        for key,value in summary(cohort,raw,checked,c).items():exact(a[key],value)
        for key,path in (('independent_receipt_sha256',output/(cohort+'-proof.json')),('production_arm_sha256',run/cohort/'results.json'),
            ('production_results_sha256',run/'results.json'),('production_supervisor_sha256',run/'supervisor.json')):assert a[key]==sha(path)
        number(a['report_worker_seconds'],min(600,elapsed));integer(a['report_peak_rss_kib'],1,ADDRESS_SPACE_BYTES//1024);arms.append(a)
    rank=lambda k:-1 if k is None else k
    predictions={'P1':True,'P2':any(a['k3']['charge_reduction_vs61']>0 for a in arms),
        'P3':any(rank(a['largest_positive_k'])>rank(a['baseline61_largest_positive_k']) for a in arms),
        'P4':any(a['k256']['charge_reduction_vs61']>0 for a in arms),'P5':any(a['k256']['integer_lower_bound']>0 for a in arms)}
    return {'schema':'gamma.global-entry-price-cap.report.v1','complete':True,'validation_loaded':False,'contract_sha256':contract,
        'arms':arms,'predictions':predictions,'population':'fixed300_fit_only','parent57_evidence_sha256':c['parent57_evidence']['sha256'],
        'parent56_evidence_sha256':c['parent56_evidence']['sha256'],'context61_evidence_sha256':c['context61_evidence']['sha256'],
        'feasibility59_sha256':c['feasibility59']['sha256'],'production_results_sha256':sha(run/'results.json'),
        'production_supervisor_sha256':sha(run/'supervisor.json'),'production_seconds':production['seconds'],'report_seconds':elapsed,
        'validation_or_cases_opened':False,'fresh_original_proof_replay':True,'private_input_files':9,
        'required_owner_constraint_applied':True,'new_qualification_jobs':0,'new_packets':0,
        'qualification':'Exact original13 source reuse; unchanged-source23 exit137 separate.',
        'coverage_scope':'Item59 seed establishes minimum feasible at-most budget3. Rows below floor are empty/null;3..256 are nonempty at-most classes, not attainment proofs.',
        'm1_claim':False,'promotion_allowed':False,'current_best_changed':False,'shared_dependencies':SHARED}


def failure_result(error):
    return {'schema':'gamma.global-entry-price-cap.report.v1','complete':False,'validation_loaded':False,'verdicts':None,
        'failure_type':type(error).__name__,'predictions':dict.fromkeys(('P1','P2','P3','P4','P5')),'promotion_allowed':False}


def markdown(result):
    if result['complete'] is not True:return '# Item66 incomplete\n\nNo verdict. Incomplete execution or replay.\n'
    lines=['# Item66 global prices with required-owner baseline','',
        'Fresh28/50/53/57 science, fresh56/61 coverage/allocation and fixed15 global prices. Headline is min(G,T61); measured min(G,T57) remains separately retained.','',
        '| Cohort | 61 k3 | Combined k3 | 61 k* | Combined k* | 61 k256 | Combined k256 | Standalone G bound |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for a in result['arms']:
        lines.append(f"| {a['cohort']} | {a['baseline61_rows'][3]['integer_lower_bound']} | {a['k3']['integer_lower_bound']} | {a['baseline61_largest_positive_k']} | {a['largest_positive_k']} | {a['baseline61_rows'][256]['integer_lower_bound']} | {a['k256']['integer_lower_bound']} | {a['standalone_global']['integer_lower_bound']} |")
    lines+=['','All257 curves, raw and integer gains, all15 lambda*B/residual/charge/bound rows and diagnostics are in results.json. k* is the largest positive defined k. Budgets below3 are empty/null. Item59 establishes nonempty at-most classes3..256, not every exact count or attainment.',
        '', 'Standalone G has no support restriction; combined positivity excludes F=10C-N<=0 only in its named fixed-source support class. Finish is excluded. Nonpositive bounds are inconclusive. Global winners have no invented allocation split.',
        '', 'Smallest minimizing global price breaks ties; all minimizers are reported. Price0 is the all-entry unpriced cap, distinct from57 owner caps. Neither endpoint selection nor its absence establishes grid adequacy.',
        '', 'No new witness, qualification, M1, validation or current-best claim. Original13 qualification reused; unchanged-source23 exit137 remains separate. Earlier61 inherited57 authority; this replay freshly reconstructs57.',
        '', 'Predictions: '+json.dumps(result['predictions'],sort_keys=True)]
    return '\n'.join(lines)+'\n'

def remove_success(output, deadline=None):
    """Minimal withdrawal only; never swallow the caller's hard deadline."""
    output = Path(output)
    for name in ('results.json', 'REPORT.md', 'results.json.pending', 'REPORT.md.pending'):
        if deadline is not None: worker_failure_guard(deadline)
        try:
            (output/name).unlink(missing_ok=True)
        except Exception:
            pass

def withdraw(output, error, deadline=None):
    """Caller supplies the absolute failure-I/O guard; hard deadlines propagate.

    Withdraw both success markers before starting potentially slow failure
    serialization/writes. Ordinary per-file errors remain independent, but a
    BaseException deadline from ANY supervisor class ends all further I/O.
    """
    output = Path(output)
    remove_success(output, deadline)
    failed = failure_result(error)
    for name, text in (('REPORT.md', markdown(failed)),
                       ('results.json', json.dumps(failed, sort_keys=True, indent=2)+'\n')):
        target = output/name
        try:
            if deadline is not None: worker_failure_guard(deadline)
            output.mkdir(parents=True, exist_ok=True)
            temporary = output/(name+'.failure')
            if deadline is not None: worker_failure_guard(deadline)
            temporary.write_text(text)
            if deadline is not None: worker_failure_guard(deadline)
            temporary.replace(target)
        except Exception:
            if deadline is not None: worker_failure_guard(deadline)
            try:
                target.unlink(missing_ok=True)
            except Exception:
                pass

def publish(output, result):
    output = Path(output)
    try:
        output.mkdir(parents=True, exist_ok=True)
        if result['complete'] is not True:
            withdraw(output, RuntimeError('incomplete'))
            return
        encoded = json.dumps(result, sort_keys=True, indent=2, allow_nan=False)+'\n'
        assert len(encoded.encode())<=b.CARRIER_MAX_BYTES,'retained carrier exceeds256MiB'
        prose = markdown(result)
        (output/'REPORT.md.pending').write_text(prose)
        (output/'results.json.pending').write_text(encoded)
        (output/'REPORT.md.pending').replace(output/'REPORT.md')
        (output/'results.json.pending').replace(output/'results.json')
        for name in ('REPORT.md.pending', 'results.json.pending'):
            (output/name).unlink(missing_ok=True)
    except BaseException as error:
        # A one-shot owner alarm has no remaining guard once it has fired.
        # Propagate that BaseException without starting even an unlink; the
        # supervisor re-arms its single absolute emergency budget before
        # withdrawal. Ordinary direct-call write errors still withdraw locally.
        if isinstance(error, Exception) or signal.getitimer(signal.ITIMER_REAL)[0] > 0:
            remove_success(output)
        raise

def worker_failure_guard(deadline):
    remaining = deadline-time.monotonic()
    if remaining <= 0: raise HardDeadline('report worker failure publication deadline')
    signal.setitimer(signal.ITIMER_REAL, remaining)

def withdraw_worker(target, failure, deadline):
    worker_failure_guard(deadline)
    try: target.unlink(missing_ok=True)
    except Exception: pass
    worker_failure_guard(deadline)
    write(target.with_name(target.stem+'-failure.json'), failure)
    worker_failure_guard(deadline)



def worker(cohort, work, run, output, deadline):
    started = BOOT_STARTED if BOOT_STARTED is not None else time.monotonic()
    phase, target, fresh = 'setup', Path(output)/(cohort+'.json'), False
    previous = signal.signal(signal.SIGALRM, _expired)
    effective = min(started+WORKER_SECONDS, deadline)
    signal.setitimer(signal.ITIMER_REAL, max(.001, effective-time.monotonic()))
    try:
        if not __debug__:
            raise RuntimeError('independent report requires assertions')
        assert cohort in COHORTS
        number(deadline)
        if time.monotonic() >= effective:
            raise HardDeadline('deadline before report setup')
        resource.setrlimit(resource.RLIMIT_AS, (ADDRESS_SPACE_BYTES,)*2)
        os.sched_setaffinity(0, {6 if cohort == 'R' else 7})
        assert not target.exists() and not (Path(output)/(cohort+'-proof.json')).exists(), 'fresh report worker artifacts required'
        fresh = True
        binding = b
        config = read(HERE/'contract.json'); config_limits(config)
        binding.check_contract(config)
        contract_hash = sha(HERE/'contract.json')
        phase = 'production_receipts'
        production, supervisor = accepted_production(run, config, contract_hash)
        raw = next(arm for arm in production['arms'] if arm['cohort'] == cohort)
        phase = 'input_identity'
        inputs = binding.load_inputs(config, Path(work), cohort, effective)
        phase = 'fresh_independent_replay'
        proof_path = Path(output)/(cohort+'-proof.json')
        checker = module('global66_independent_worker', HERE/'independent.py')
        checked = replay(cohort, inputs, raw, checker, config)
        write(proof_path, checked)
        result = summary(cohort, raw, checked, config)
        result.update(independent_receipt_sha256=sha(proof_path),
                      production_arm_sha256=sha(Path(run)/cohort/'results.json'),
                      production_results_sha256=sha(Path(run)/'results.json'),
                      production_supervisor_sha256=sha(Path(run)/'supervisor.json'),
                      report_worker_seconds=time.monotonic()-started,
                      report_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        number(result['report_worker_seconds'], WORKER_SECONDS)
        integer(result['report_peak_rss_kib'], 1, ADDRESS_SPACE_BYTES//1024)
        phase = 'worker_publication'
        if time.monotonic() >= effective:
            raise HardDeadline('report deadline before worker publication')
        write(target, result)
        if time.monotonic() >= effective:
            raise HardDeadline('report deadline after worker publication')
        return result
    except BaseException as error:
        if fresh:
            emergency_deadline = min(time.monotonic()+10, effective+10)
            withdraw_worker(target, {**failure_result(error), 'phase': phase,
                            'seconds': time.monotonic()-started}, emergency_deadline)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cohort', choices=COHORTS, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--deadline', type=float, required=True)
    args = parser.parse_args()
    worker(args.cohort, args.work, args.run, args.output, args.deadline)
