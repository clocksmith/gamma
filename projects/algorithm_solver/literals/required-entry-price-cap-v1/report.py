"""Fresh priced-prefix required-owner replay; original nine inputs only after accepted production."""
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
priced63=module('required68_pure_report63',HERE.parent/'entry-price-path-cap-v1/report.py')
# Only shape/scientific/diagnostics/summary are used; no parent loader or worker.
priced63.HERE=HERE.parent/'entry-price-path-cap-v1'
prior=priced63.prior
allocation=module('required68_allocation61',HERE.parent/'required-owner-cap-v1/allocation.py')
exact=prior.exact;shaped=prior.shaped;digest=prior.digest;integer=prior.integer;number=prior.number
sha=b.sha;write=b.write;config_limits=prior.config_limits

def read(path):
    path=Path(path).absolute()
    assert path.resolve()==path and path.is_file(),'direct retained carrier required'
    return b.read(path)

SHARED=('Original source/parser and item33 Index/verifier; unchanged63 production/independent kernels and50/53/57 ancestry. '
 'Fresh56 trie/AC coverage with every Boolean recurrence; two required allocations use61 heap versus independent full sort. '
 'No66 global-price mechanism or private ancestral receipt is used.')
ROW_EXTRA=('baseline61_charge','baseline63_charge','comparison_max_charge','comparison_max_integer_lower_bound',
 'charge_reduction_vs61','integer_bound_gain_vs61','charge_reduction_vs63','integer_bound_gain_vs63',
 'charge_reduction_vsmax','integer_bound_gain_vsmax')


def scientific(proof):
    return {'priced':priced63.scientific(proof['priced']),
        'coverage':{key:proof['coverage'][key] for key in b.coverage_report().COMMON_FIELDS},
        'baseline61':proof['baseline61'],'required':proof['required'],'rows':proof['rows']}


def combined_rows(priced,baseline61,required):
    """Independent comparison-max arithmetic; production integration is not called."""
    tight=priced['base57']['base']['tightened'];L=sum(tight['path_numerators'].values());D=tight['denominator']
    r=required['coverage_floor'];assert baseline61['coverage_floor']==r
    assert len(required['rows'])==len(baseline61['rows'])==len(priced['rows'])>0
    rows=[]
    for k,(row,old61,old63) in enumerate(zip(required['rows'],baseline61['rows'],priced['rows'])):
        value=dict(row)
        if k<r:
            assert row['empty_by_required_owners'] is old61['empty_by_required_owners'] is True
            value.update(dict.fromkeys(ROW_EXTRA))
        else:
            assert row['empty_by_required_owners'] is old61['empty_by_required_owners'] is False
            bestcharge=min(old61['charge'],old63['charge']);lower,remainder=divmod(L-bestcharge,D);bestbound=lower+int(remainder!=0)
            assert bestbound==max(old61['integer_lower_bound'],old63['integer_lower_bound'])
            assert row['charge']<=bestcharge
            value.update(baseline61_charge=old61['charge'],baseline63_charge=old63['charge'],
                comparison_max_charge=bestcharge,comparison_max_integer_lower_bound=bestbound,
                charge_reduction_vs61=old61['charge']-row['charge'],integer_bound_gain_vs61=row['integer_lower_bound']-old61['integer_lower_bound'],
                charge_reduction_vs63=old63['charge']-row['charge'],integer_bound_gain_vs63=row['integer_lower_bound']-old63['integer_lower_bound'],
                charge_reduction_vsmax=bestcharge-row['charge'],integer_bound_gain_vsmax=row['integer_lower_bound']-bestbound)
        rows.append(value)
    return rows


def shape(proof,geometry,direction='price_prefix_schedule'):
    assert set(proof)=={'priced','coverage','baseline61','required','rows','digests'}
    p=proof['priced'];priced63.shape(p,geometry,direction);base=p['base57'];tight=base['base']['tightened']
    ids=set(base['owner_caps']);cov=proof['coverage'];covdir='prefix_reachable' if direction=='price_prefix_schedule' else 'suffix_reachable'
    expected={'old_pool_entries':len(cov['owner_classes']),'class_counts':tight['class_counts'],
        'old_occurrences':tight['old_occurrences'],'old_occurrence_order_sha256':tight['occurrence_sha256'],'geometry':geometry}
    b.coverage_report().proof_shape(cov,expected,ids,covdir)
    L=sum(tight['path_numerators'].values());D=tight['denominator'];forced=cov['forced_source_ids']
    # Full independent finite allocations are cheap enough to verify at pre-read shape validation too.
    old=shaped(allocation.independent(base['capped_prefixes'],base['shared_prefix'],forced,L,D))
    new=shaped(allocation.independent(p['priced_prefixes'],p['shared_prefix'],forced,L,D))
    exact(proof['baseline61'],old);exact(proof['required'],new)
    exact(proof['rows'],combined_rows(p,old,new))
    assert set(proof['digests'])=={key+'_sha256' for key in ('priced','coverage','baseline61','required','rows')}
    for key in ('priced','coverage','baseline61','required','rows'):assert proof['digests'][key+'_sha256']==digest(proof[key])


def historical_priced(proof,c,cohort,checked=None):
    p=proof['priced'];old=c['parent63_arms'][cohort]
    assert digest(p)==old['production_proof_sha256']
    assert digest(priced63.scientific(p))==old['scientific_proof_sha256']
    exact(p['digests'],old['digests']);exact(p['rows'],old['rows']);exact(p['deltas_vs57'],old['deltas_vs57'])
    exact(p['lambda_family'],old['lambda_family']);exact(priced63.diagnostics(p),old['price_diagnostics'])
    exact(p['work'],old['production_work']);exact(p['base57']['work'],old['baseline57_production_work'])
    exact(p['base57']['base']['work'],old['baseline53_production_work'])
    assert digest(prior.scientific(p['base57']))==old['baseline57_scientific_sha256']
    exact(p['base57']['base']['digests'],old['baseline53_paired_digests'])
    if checked is not None:
        v=checked['priced'];assert digest(priced63.scientific(v))==old['scientific_proof_sha256']
        exact(v['digests'],old['independent_digests']);exact(v['work'],old['report_work'])
        exact(v['base57']['work'],old['baseline57_report_work']);exact(v['base57']['base']['work'],old['baseline53_report_work'])
        exact(priced63.diagnostics(v),old['price_diagnostics'])


def accepted_production(run,c,contract):
    config_limits(c);b.verify_parent50(c);b.verify_parent53(c);b.verify_parent57(c);b.verify_feasibility(c)
    b.verify_parent56(c);b.verify_context61(c);b.verify_parent63(c)
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
        assert raw['schema']=='gamma.required-entry-price-cap.arm.v1' and raw['complete'] is True and raw['validation_loaded'] is False
        assert raw['contract_sha256']==contract;number(raw['seconds'],min(600,result['seconds']));integer(raw['peak_rss_kib'],1,ADDRESS_SPACE_BYTES//1024)
        assert set(raw['phase_seconds'])=={'input','proof'}
        for value in raw['phase_seconds'].values():number(value,raw['seconds'])
        assert sum(raw['phase_seconds'].values())<=raw['seconds']
        exact(raw['full_shape'],c['full_shape'][cohort]);shape(raw['proof'],raw['full_shape'])
        historical_required(raw['proof'],c,cohort);historical_priced(raw['proof'],c,cohort)
        base=raw['proof']['priced']['base57'];assert set(base['owner_caps'])==set(map(str,c['fit_ids']))
        assert digest(raw['bindings'])==c['parent50_arms'][cohort]['bindings_sha256']
        assert raw['bindings']['source_hashes_sha256']==c['parent57_arms'][cohort]['source_identity_sha256']
        assert raw['bindings']['bans_sha256']==c['parent57_arms'][cohort]['banned_set_sha256']
        assert digest(prior.scientific(base))==c['parent57_arms'][cohort]['scientific_proof_sha256']
        assert digest(base)==c['parent57_arms'][cohort]['production_proof_sha256']
        exact(raw,read(run/cohort/'results.json'))
    return result,sup


def paired_shape(production,checked,geometry):
    shape(checked,geometry,'price_suffix_schedule');exact(scientific(production),scientific(checked))
    p=production['priced'];v=checked['priced'];prior.independent_shape(p['base57'],v['base57'],geometry)
    assert v['production_forward_schedule_sha256']==digest(p['price_prefix_schedule'])


def replay(cohort,inputs,raw,checker,c):
    exact(raw['bindings'],shaped(inputs['bindings']));exact(raw['full_shape'],inputs['geometry'])
    p=raw['proof'];priced=p['priced'];shape(p,raw['full_shape'])
    checked_priced=shaped(checker.check(inputs['texts'],inputs['banned'],inputs['pool'],inputs['q'],inputs['seed'],inputs['alphabet'],inputs['denominator'],
        expected_source_hashes=inputs['source_hashes'],expected_old_banned=inputs['banned'],expected_old_certificate=inputs['parent_certificate'],
        expected_occurrence_sha256=c['parent50_arms'][cohort]['old_occurrence_order_sha256'],
        expected_base57_prefix_schedule=priced['base57']['owner_prefix_schedule'],expected_price_prefix_schedule=priced['price_prefix_schedule'],
        expected_count_streams=priced['count_streams'],expected_price_caps=priced['price_caps']))
    assert len(inputs['alphabet'])==len(set(inputs['alphabet']))==96 and all(len(s)==1 for s in inputs['alphabet'])
    assert set(inputs['alphabet'])<=set(inputs['pool']) and not set(inputs['pool'])&set(inputs['banned'])
    assert all(set(text)<=set(inputs['alphabet']) for text in inputs['texts'].values())
    cov=shaped(b.coverage().replay(inputs['texts'],inputs['pool'],inputs['banned']))
    for key in b.coverage_report().COMMON_FIELDS:exact(p['coverage'][key],cov[key])
    b.coverage_report().check_vectors(inputs['texts'],inputs['pool'],p['coverage'],cov)
    base=checked_priced['base57'];tight=base['base']['tightened'];L=sum(tight['path_numerators'].values());D=tight['denominator']
    baseline61=shaped(allocation.independent(base['capped_prefixes'],base['shared_prefix'],cov['forced_source_ids'],L,D))
    required=shaped(allocation.independent(checked_priced['priced_prefixes'],checked_priced['shared_prefix'],cov['forced_source_ids'],L,D))
    checked={'priced':checked_priced,'coverage':cov,'baseline61':baseline61,'required':required,
        'rows':combined_rows(checked_priced,baseline61,required)}
    checked['digests']={key+'_sha256':digest(value) for key,value in checked.items()}
    paired_shape(p,checked,raw['full_shape']);historical_required(checked,c,cohort);historical_priced(p,c,cohort,checked)
    fake={**raw,'proof':priced['base57']}
    prior.compare53(fake,inputs,base,raw['full_shape'],c['parent53_arms'][cohort])
    basepublic=prior.prior.sanitize(cohort,inputs,{**raw,'proof':priced['base57']['base']},base['base'],raw['full_shape'])
    prior.prior.compare50(cohort,basepublic,base['base']['lifted'],c['parent50_arms'][cohort])
    historical=c['parent57_arms'][cohort]
    assert digest(prior.scientific(base))==historical['scientific_proof_sha256']
    assert digest(priced['base57'])==historical['production_proof_sha256']
    assert digest(base['owner_suffix_schedule'])==historical['independent_suffix_schedule_sha256']
    for key in ('rows','deltas_vs53'):exact(base[key],historical[key])
    return checked

def historical_required(proof,c,cohort):
    """Match scientific commitments, not the predecessor's private read receipts."""
    g=proof['priced'];base=g['base57'];cov=proof['coverage'];req=proof['baseline61'];old=c['context61_arms'][cohort]
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



def positive(rows):
    return max((r['k'] for r in rows if r['integer_lower_bound'] is not None and r['integer_lower_bound']>0),default=None)


def max_positive(*values):
    return max((v for v in values if v is not None),default=None)


def comparison_rows(rows):
    return [{'k':row['k'],'empty_by_required_owners':row['empty_by_required_owners'],
        'charge':row['comparison_max_charge'],
        'numerator':None if row['empty_by_required_owners'] else row['numerator']-row['charge_reduction_vsmax'],
        'integer_lower_bound':row['comparison_max_integer_lower_bound']} for row in rows]


def summary(cohort,raw,checked,c):
    p=raw['proof'];priced=p['priced'];base=priced['base57'];tight=base['base']['tightened'];rows=p['rows']
    cov=checked['coverage'];req=checked['required'];old61=checked['baseline61'];r=req['coverage_floor']
    star61=positive(old61['rows']);star63=positive(priced['rows'])
    return {'schema':'gamma.required-entry-price-cap.report-arm.v1','cohort':cohort,'complete':True,'validation_loaded':False,
        'contract_sha256':raw['contract_sha256'],'parent57_evidence_sha256':c['parent57_evidence']['sha256'],
        'parent56_evidence_sha256':c['parent56_evidence']['sha256'],'context61_evidence_sha256':c['context61_evidence']['sha256'],
        'parent63_evidence_sha256':c['parent63_evidence']['sha256'],
        'source_identity_sha256':raw['bindings']['source_hashes_sha256'],'banned_set_sha256':raw['bindings']['bans_sha256'],
        'bindings_sha256':digest(raw['bindings']),'parent_certificate_sha256':c['parent57_arms'][cohort]['parent_certificate_sha256'],
        'geometry':raw['full_shape'],'class_counts':tight['class_counts'],'denominator':tight['denominator'],
        'path_numerator':sum(tight['path_numerators'].values()),'old_occurrences':tight['old_occurrences'],
        'baseline57_scientific_sha256':digest(prior.scientific(base)),'baseline53_paired_digests':base['base']['digests'],
        'baseline63_scientific_sha256':digest(priced63.scientific(priced)),'baseline63_production_proof_sha256':digest(priced),
        'production_proof_sha256':digest(p),'scientific_proof_sha256':digest(scientific(checked)),
        'digests':p['digests'],'independent_digests':checked['digests'],
        'priced_digests':priced['digests'],'independent_priced_digests':checked['priced']['digests'],
        'rows':rows,'baseline61_rows':old61['rows'],'baseline63_rows':priced['rows'],'baseline57_rows':base['rows'],
        'comparison_max_rows':comparison_rows(rows),'k3':rows[3],'k256':rows[256],'largest_positive_k':positive(rows),
        'baseline61_largest_positive_k':star61,'baseline63_largest_positive_k':star63,
        'maximum_predecessor_largest_positive_k':max_positive(star61,star63),
        'comparison_max_largest_positive_k':positive(comparison_rows(rows)),
        'strict_charge_budgets':sum(row['charge_reduction_vsmax'] is not None and row['charge_reduction_vsmax']>0 for row in rows),
        'strict_integer_budgets':sum(row['integer_bound_gain_vsmax'] is not None and row['integer_bound_gain_vsmax']>0 for row in rows),
        'strict_charge_budgets_vs61':sum(row['charge_reduction_vs61'] is not None and row['charge_reduction_vs61']>0 for row in rows),
        'strict_charge_budgets_vs63':sum(row['charge_reduction_vs63'] is not None and row['charge_reduction_vs63']>0 for row in rows),
        'coverage_floor':r,'empty_budgets':[row['k'] for row in rows if row['empty_by_required_owners']],
        'minimum_feasible_one_owner_budget':3,'forced_source_ids_sha256':digest(cov['forced_source_ids']),
        'coverage_occurrences':cov['occurrences'],'coverage_occurrence_sha256':cov['occurrence_sha256'],
        'production_coverage_prefix_sha256':digest(p['coverage']['prefix_reachable']),
        'independent_coverage_suffix_sha256':digest(cov['suffix_reachable']),
        'baseline61_allocation_sha256':digest(old61),'required_allocation_sha256':digest(req),
        'baseline61_mandatory_value':old61['mandatory_value'],'mandatory_value':req['mandatory_value'],
        'lambda_family':priced['lambda_family'],'price_diagnostics':priced63.diagnostics(checked['priced']),
        'production_work':priced['work'],'report_work':checked['priced']['work'],
        'baseline57_production_work':base['work'],'baseline57_report_work':checked['priced']['base57']['work'],
        'baseline53_production_work':base['base']['work'],'baseline53_report_work':checked['priced']['base57']['base']['work'],
        'fresh_coverage_work':{'source_positions':raw['full_shape']['source_characters'],'occurrences_per_direction':cov['occurrences'],
            'additional_recurrence_AC_pass':True,'forced_owners':r},
        'fresh_allocation_work':{'allocations_per_direction':2,'finite_marginals_per_allocation':sum(len(v)-1 for v in base['capped_prefixes'].values()),
            'residual_marginals_per_allocation':sum(len(v)-1 for v in base['capped_prefixes'].values())-r},
        'production_seconds':raw['seconds'],'production_peak_rss_kib':raw['peak_rss_kib'],
        'production_phase_seconds_sha256':digest(raw['phase_seconds']),
        'all257_independently_replayed':True,'all63_forward_recurrences_checked':True,'all57_forward_recurrences_checked':True,
        'all_coverage_recurrences_checked':True,'historical63_reconstructed':True,'historical57_reconstructed':True,
        'fresh_original_proof_replay':True,'fresh_forced_owner_replay':True,'fresh_constrained_allocation_replay':True,
        'parent61_inherited57_authority':True,'shared_dependencies':SHARED}


ARM_FIELDS=set(('schema cohort complete validation_loaded contract_sha256 parent57_evidence_sha256 parent56_evidence_sha256 '
 'context61_evidence_sha256 parent63_evidence_sha256 source_identity_sha256 banned_set_sha256 bindings_sha256 parent_certificate_sha256 '
 'geometry class_counts denominator path_numerator old_occurrences baseline57_scientific_sha256 baseline53_paired_digests '
 'baseline63_scientific_sha256 baseline63_production_proof_sha256 production_proof_sha256 scientific_proof_sha256 digests independent_digests '
 'priced_digests independent_priced_digests rows baseline61_rows baseline63_rows baseline57_rows comparison_max_rows k3 k256 largest_positive_k '
 'baseline61_largest_positive_k baseline63_largest_positive_k maximum_predecessor_largest_positive_k comparison_max_largest_positive_k '
 'strict_charge_budgets strict_integer_budgets strict_charge_budgets_vs61 strict_charge_budgets_vs63 coverage_floor empty_budgets '
 'minimum_feasible_one_owner_budget forced_source_ids_sha256 coverage_occurrences coverage_occurrence_sha256 '
 'production_coverage_prefix_sha256 independent_coverage_suffix_sha256 baseline61_allocation_sha256 required_allocation_sha256 '
 'baseline61_mandatory_value mandatory_value lambda_family price_diagnostics production_work report_work '
 'baseline57_production_work baseline57_report_work baseline53_production_work baseline53_report_work fresh_coverage_work fresh_allocation_work '
 'production_seconds production_peak_rss_kib production_phase_seconds_sha256 all257_independently_replayed all63_forward_recurrences_checked '
 'all57_forward_recurrences_checked all_coverage_recurrences_checked historical63_reconstructed historical57_reconstructed '
 'fresh_original_proof_replay fresh_forced_owner_replay fresh_constrained_allocation_replay parent61_inherited57_authority shared_dependencies '
 'independent_receipt_sha256 production_arm_sha256 production_results_sha256 production_supervisor_sha256 report_worker_seconds report_peak_rss_kib').split())


def combine(run,output,c,elapsed,returncodes):
    number(elapsed,1200);exact(returncodes,[0,0]);run,output=Path(run),Path(output)
    assert not (output/'failure.json').exists();contract=sha(HERE/'contract.json');production,sup=accepted_production(run,c,contract);arms=[]
    for cohort,raw in zip(COHORTS,production['arms']):
        assert not (output/(cohort+'-failure.json')).exists()
        checked=read(output/(cohort+'-proof.json'));a=read(output/(cohort+'.json'));assert set(a)==ARM_FIELDS
        paired_shape(raw['proof'],checked,raw['full_shape']);historical_required(checked,c,cohort);historical_priced(raw['proof'],c,cohort,checked)
        for key,value in summary(cohort,raw,checked,c).items():exact(a[key],value)
        for key,path in (('independent_receipt_sha256',output/(cohort+'-proof.json')),('production_arm_sha256',run/cohort/'results.json'),
            ('production_results_sha256',run/'results.json'),('production_supervisor_sha256',run/'supervisor.json')):assert a[key]==sha(path)
        number(a['report_worker_seconds'],min(600,elapsed));integer(a['report_peak_rss_kib'],1,ADDRESS_SPACE_BYTES//1024);arms.append(a)
    rank=lambda k:-1 if k is None else k
    predictions={'P1':True,'P2':any(a['k3']['charge_reduction_vsmax']>0 for a in arms),
        'P3':any(rank(a['largest_positive_k'])>rank(a['maximum_predecessor_largest_positive_k']) for a in arms),
        'P4':any(a['k256']['charge_reduction_vsmax']>0 for a in arms),'P5':any(a['k256']['integer_lower_bound']>0 for a in arms)}
    return {'schema':'gamma.required-entry-price-cap.report.v1','complete':True,'validation_loaded':False,'contract_sha256':contract,
        'arms':arms,'predictions':predictions,'population':'fixed300_fit_only','parent57_evidence_sha256':c['parent57_evidence']['sha256'],
        'parent56_evidence_sha256':c['parent56_evidence']['sha256'],'context61_evidence_sha256':c['context61_evidence']['sha256'],
        'parent63_evidence_sha256':c['parent63_evidence']['sha256'],'feasibility59_sha256':c['feasibility59']['sha256'],
        'production_results_sha256':sha(run/'results.json'),'production_supervisor_sha256':sha(run/'supervisor.json'),
        'production_seconds':production['seconds'],'report_seconds':elapsed,
        'validation_or_cases_opened':False,'fresh_original_proof_replay':True,'private_input_files':9,
        'required_owner_constraint_applied':True,'priced_prefix_constraint_applied':True,'global_price_constraint_applied':False,
        'new_qualification_jobs':0,'new_packets':0,'qualification':'Exact original13 source reuse; unchanged-source23 exit137 separate.',
        'coverage_scope':'Item59 seed establishes minimum feasible at-most budget3. Rows below floor are empty/null;3..256 are nonempty at-most classes, not attainment proofs.',
        'm1_claim':False,'promotion_allowed':False,'current_best_changed':False,'shared_dependencies':SHARED}


def failure_result(error):
    return {'schema':'gamma.required-entry-price-cap.report.v1','complete':False,'validation_loaded':False,'verdicts':None,
        'failure_type':type(error).__name__,'predictions':dict.fromkeys(('P1','P2','P3','P4','P5')),'promotion_allowed':False}


def markdown(result):
    if result['complete'] is not True:return '# Item68 incomplete\n\nNo verdict. Incomplete execution or replay.\n'
    lines=['# Item68 required slots with priced owner prefixes','',
        'Fresh63/57/53/50 reconstruction and fresh56 coverage. Both61 and68 allocations are independently replayed. Registered gains compare68 with the pointwise maximum predecessor bound.','',
        '| Cohort | 61 k3 | 63 k3 | Max k3 | 68 k3 | 61 k* | 63 k* | 68 k* | 61 k256 | 63 k256 | Max k256 | 68 k256 |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for a in result['arms']:
        lines.append(f"| {a['cohort']} | {a['baseline61_rows'][3]['integer_lower_bound']} | {a['baseline63_rows'][3]['integer_lower_bound']} | {a['k3']['comparison_max_integer_lower_bound']} | {a['k3']['integer_lower_bound']} | {a['baseline61_largest_positive_k']} | {a['baseline63_largest_positive_k']} | {a['largest_positive_k']} | {a['baseline61_rows'][256]['integer_lower_bound']} | {a['baseline63_rows'][256]['integer_lower_bound']} | {a['k256']['comparison_max_integer_lower_bound']} | {a['k256']['integer_lower_bound']} |")
    lines+=['','All257 curves and raw/integer gains against61,63 and their maximum are in results.json. k* is the largest positive k. Budgets below3 are empty/null; historical63 numerical rows there are not68 feasible-class claims.',
        '', 'Item59 establishes nonempty at-most classes3..256, not every exact count or attainment. A positive bound excludes F=10C-N<=0 only in its named fixed-source support class; Finish is excluded. Nonpositive bounds are inconclusive.',
        '', 'Fixed15 prices and descriptive63 diagnostics are preserved. Their finite grid is not claimed adequate. Mandatory zero-value owner slots consume capacity. No66 global-price mechanism is applied.',
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
        checker = module('required68_independent_worker', HERE.parent/'entry-price-path-cap-v1/independent.py')
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
