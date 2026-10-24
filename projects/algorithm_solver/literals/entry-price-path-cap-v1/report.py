"""Fresh fixed-price replay; original nine inputs only after accepted production."""
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
prior=module('entry63_report57',HERE.parent/'owner-path-cap-v1/report.py')
exact=prior.exact;shaped=prior.shaped;digest=prior.digest;integer=prior.integer;number=prior.number
sha=b.sha;write=b.write;config_limits=prior.config_limits

def read(path):
    path=Path(path).absolute()
    assert path.resolve()==path and path.is_file(),'direct retained carrier required'
    return b.read(path)
COMMON=('lambda_family','count_streams','price_caps','affine_envelopes','priced_prefixes',
        'one_owner_prefix','marginal_choices','shared_prefix','rows','deltas_vs57')
PROD_WORK=('baseline57_reconstructions','additional53_contexts','structural_groups','terminal_positions_checked',
 'ancestor_group_visits','candidate_owner_depths','allowed_owner_endpoints','banned_owner_endpoints',
 'multiplicity_cache_entries','multiplicity_divisions','q_evaluations','price_residual_evaluations',
 'forward_arc_candidates','forward_skip_candidates','count_stream_records','prefix_price_evaluations',
 'allocation_heap_offers','allocation_heap_pops')
AUDIT_WORK=('baseline57_reconstructions','additional_old_contexts','old_occurrences_replayed','old_bellman_edges_checked',
 'support_suffix_positions_checked','support_groups_classified','old_occurrences_reclassified',
 'old_owned_occurrence_counts_checked','banned_occurrences_matched','z_input_symbols','z_character_comparisons',
 'z_histogram_cells','endpoints_inspected','banned_endpoints_skipped','shared_allowed_endpoints_skipped',
 'one_owner_occurrences','count_records','q_evaluations','price_residual_evaluations','backward_candidates',
 'production_forward_candidates','production_forward_positions_checked','prefix_price_evaluations','allocation_marginals_sorted')
SHARED='Original source/parser and item33 Index; unchanged57 production/independent baselines and53 potential contexts. Independent AC support, numeric Z counts, backward schedules, every forward recurrence and full marginal-sort allocation.'


def scientific(proof):
    return {'schema':proof['schema'],'base57':prior.scientific(proof['base57']),**{key:proof[key] for key in COMMON}}


def shape(proof,geometry,direction='price_prefix_schedule'):
    """Strict public-checkable carrier algebra; source recurrence replay follows."""
    assert direction in ('price_prefix_schedule','price_suffix_schedule')
    isprod=direction=='price_prefix_schedule'
    extras=set() if isprod else {'production_forward_schedule_checked','production_forward_schedule_sha256','shared_dependency','scalar_replay'}
    assert set(proof)=={'schema','base57','digests','work',direction,*COMMON}|extras
    assert proof['schema']=='gamma.entry-price-path-cap.supplied.v1'
    base=proof['base57'];ids=set(base['owner_caps'])
    if isprod:prior.owner_shape(base,geometry)
    D=integer(base['base']['tightened']['denominator'],1)
    L=sum(base['base']['tightened']['path_numerators'].values())
    prices=[0]+[D*2**r for r in range(14)];exact(proof['lambda_family'],prices);K=len(prices)
    positions=endpoints=arcs=0;marginals=[]
    for key in ('count_streams','price_caps','affine_envelopes','priced_prefixes',direction):assert set(proof[key])==ids
    for pid in sorted(ids):
        caps=proof['price_caps'][pid];vectors=proof[direction][pid]
        assert type(caps) is list and len(caps)==K and type(vectors) is list and len(vectors)==K
        for v in caps:integer(v,0)
        assert caps==sorted(caps,reverse=True) and caps[0]==base['owner_caps'][pid]
        n=len(vectors[0])-1;assert n>0;positions+=n;endpoints+=n*(n+1)//2
        for cap,vec in zip(caps,vectors):
            assert type(vec) is list and len(vec)==n+1
            for v in vec:integer(v,0)
            assert vec[0 if isprod else -1]==0 and vec[-1 if isprod else 0]==cap
            assert vec==sorted(vec,reverse=not isprod)
        exact(vectors[0],base['owner_prefix_schedule' if isprod else 'owner_suffix_schedule'][pid])
        streams=proof['count_streams'][pid];assert type(streams) is list and len(streams)==n
        for start,stream in enumerate(streams):
            assert set(stream)=={'arcs','sha256'}
            arcs+=integer(stream['arcs'],0,n-start);prior.hash_string(stream['sha256'])
            if stream['arcs']==0:assert stream['sha256']==hashlib.sha256(b'').hexdigest()
        A=base['owner_prefixes'][pid];f=proof['priced_prefixes'][pid]
        envelope=[min(price*t+cap for price,cap in zip(prices,caps)) for t in range(len(A))]
        exact(proof['affine_envelopes'][pid],envelope);exact(f,[min(a,v) for a,v in zip(A,envelope)])
        assert len(f)==min(256,base['owner_entry_counts'][pid])+1 and f[0]==0
        increments=[integer(v-u,0) for u,v in zip(f,f[1:])]
        assert increments==sorted(increments,reverse=True)
        assert all(u<=v for u,v in zip(f,base['capped_prefixes'][pid]))
        marginals.extend((value,pid,rank) for rank,value in enumerate(increments,1))
    assert positions==geometry['source_characters']
    selected=sorted(marginals,key=lambda v:(-v[0],v[1],v[2]))[:256]
    one=[0];choices=[]
    for value,pid,rank in selected:one.append(one[-1]+value);choices.append([pid,rank,value])
    exact(proof['one_owner_prefix'],one);exact(proof['marginal_choices'],choices)
    exact(proof['shared_prefix'],base['shared_prefix']);shared=proof['shared_prefix']
    assert len(proof['rows'])==len(proof['deltas_vs57'])==257
    for k,(row,old,delta) in enumerate(zip(proof['rows'],base['rows'],proof['deltas_vs57'])):
        charge,j=max(((one[j]+shared[min(256-j,len(shared)-1)],j) for j in range(min(k,len(one)-1)+1)),key=lambda v:(v[0],-v[1]))
        num=L-charge
        exact(row,{'k':k,'charge':charge,'one_owner_slots':j,'shared_slots':min(256-j,len(shared)-1),
                   'numerator':num,'integer_lower_bound':-(-num//D)})
        exact(delta,{'k':k,'charge_reduction':old['charge']-charge,'integer_bound_gain':row['integer_lower_bound']-old['integer_lower_bound']})
        assert delta['charge_reduction']>=0
    assert set(proof['digests'])=={key+'_sha256' for key in (*COMMON,direction)}|{'base57_sha256'}
    for key in (*COMMON,direction):assert proof['digests'][key+'_sha256']==digest(proof[key])
    assert proof['digests']['base57_sha256']==digest(prior.scientific(base))
    w=proof['work'];assert set(w)==set(PROD_WORK if isprod else AUDIT_WORK)
    for v in w.values():integer(v,0)
    assert w['baseline57_reconstructions']==1 and w['q_evaluations']==arcs
    assert w['price_residual_evaluations']==K*arcs
    assert w['prefix_price_evaluations']==K*sum(map(len,base['owner_prefixes'].values()))
    if isprod:
        assert w['additional53_contexts']==1
        assert w['structural_groups']==geometry['full_groups'] and w['terminal_positions_checked']==positions
        assert w['ancestor_group_visits']<=endpoints and w['candidate_owner_depths']<=endpoints
        assert w['allowed_owner_endpoints']==w['count_stream_records']==arcs
        assert w['candidate_owner_depths']==arcs+w['banned_owner_endpoints']
        assert w['banned_owner_endpoints']<=geometry['exact_ban_occurrences']
        assert w['multiplicity_cache_entries']<=geometry['full_groups']
        assert w['multiplicity_divisions']==K*w['multiplicity_cache_entries']
        assert w['forward_arc_candidates']==K*arcs and w['forward_skip_candidates']==K*positions
        assert arcs==base['work']['schedule_one_owner_occurrences']
        assert w['allocation_heap_pops']==len(selected)
        offers=sum(len(v)>1 for v in proof['priced_prefixes'].values())
        offers+=sum(rank+1<len(proof['priced_prefixes'][pid]) for pid,rank,_ in choices)
        assert w['allocation_heap_offers']==offers
    else:
        assert w['additional_old_contexts']==1
        assert w['old_occurrences_replayed']==w['old_bellman_edges_checked']==w['old_occurrences_reclassified']==base['base']['tightened']['old_occurrences']
        assert w['support_suffix_positions_checked']==positions and w['support_groups_classified']==geometry['full_groups']
        assert w['endpoints_inspected']==endpoints
        assert w['banned_occurrences_matched']==w['banned_endpoints_skipped']==geometry['exact_ban_occurrences']
        assert w['shared_allowed_endpoints_skipped']+w['banned_endpoints_skipped']+arcs==endpoints
        assert w['one_owner_occurrences']==w['count_records']==arcs==base['work']['schedule_occurrences_admitted']
        assert w['backward_candidates']==w['production_forward_candidates']==K*arcs
        assert w['production_forward_positions_checked']==K*positions
        assert w['allocation_marginals_sorted']==len(marginals)
        assert proof['production_forward_schedule_checked'] is True
        prior.hash_string(proof['production_forward_schedule_sha256'])
        assert type(proof['shared_dependency']) is type(proof['scalar_replay']) is str


def diagnostics(proof):
    """Descriptive only; no owner IDs or rank arrays escape this aggregation."""
    prices=proof['lambda_family'];hist=[0]*len(prices);below=ties=minimizers=0
    for pid,A in proof['base57']['owner_prefixes'].items():
        caps=proof['price_caps'][pid]
        for t in range(1,len(A)):
            if A[t]-A[t-1]<=0:continue
            values=[price*t+cap for price,cap in zip(prices,caps)];best=min(values)
            selected=[i for i,value in enumerate(values) if value==best]
            hist[selected[0]]+=1;ties+=int(len(selected)>1);minimizers+=len(selected);below+=int(best<A[t])
    denominator=sum(hist);counts={'zero':hist[0],'interior':sum(hist[1:-1]),'maximum':hist[-1]}
    return {'denominator':denominator,'histogram':hist,'category_counts':counts,
            'category_shares':{key:value/denominator if denominator else None for key,value in counts.items()},
            'affine_strict_below_A':below,'tied_rank_count':ties,'minimizer_count':minimizers}


def accepted_production(run,c,contract):
    config_limits(c);b.verify_parent50(c);b.verify_parent53(c);b.verify_parent57(c);b.verify_feasibility(c);b.verify_context61(c)
    run=Path(run);assert not (run/'failure.json').exists()
    result,sup=read(run/'results.json'),read(run/'supervisor.json')
    assert set(result)=={'complete','validation_loaded','contract_sha256','seconds','arms'}
    assert set(sup)=={'complete','phase','contract_sha256','elapsed','cleanup_seconds','returncodes'}
    assert result['complete'] is sup['complete'] is True and result['validation_loaded'] is False
    assert sup['phase']=='production' and result['contract_sha256']==sup['contract_sha256']==contract
    exact(sup['returncodes'],[0,0]);number(sup['elapsed'],1200);number(sup['cleanup_seconds'],10);number(result['seconds'],sup['elapsed'])
    assert [a['cohort'] for a in result['arms']]==list(COHORTS)
    for raw in result['arms']:
        cohort=raw['cohort'];assert not (run/cohort/'failure.json').exists() and not (run/(cohort+'-failure.json')).exists()
        assert set(raw)=={'schema','cohort','complete','validation_loaded','contract_sha256','bindings','full_shape','proof','phase_seconds','seconds','peak_rss_kib'}
        assert raw['schema']=='gamma.entry-price-path-cap.arm.v1' and raw['complete'] is True and raw['validation_loaded'] is False
        assert raw['contract_sha256']==contract;number(raw['seconds'],min(600,result['seconds']));integer(raw['peak_rss_kib'],1,ADDRESS_SPACE_BYTES//1024)
        assert set(raw['phase_seconds'])=={'input','proof'}
        for v in raw['phase_seconds'].values():number(v,raw['seconds'])
        assert sum(raw['phase_seconds'].values())<=raw['seconds']
        exact(raw['full_shape'],c['full_shape'][cohort]);shape(raw['proof'],raw['full_shape'])
        assert set(raw['proof']['base57']['owner_caps'])==set(map(str,c['fit_ids']))
        assert digest(raw['bindings'])==c['parent50_arms'][cohort]['bindings_sha256']
        assert raw['bindings']['source_hashes_sha256']==c['parent57_arms'][cohort]['source_identity_sha256']
        assert raw['bindings']['bans_sha256']==c['parent57_arms'][cohort]['banned_set_sha256']
        assert digest(prior.scientific(raw['proof']['base57']))==c['parent57_arms'][cohort]['scientific_proof_sha256']
        assert digest(raw['proof']['base57'])==c['parent57_arms'][cohort]['production_proof_sha256']
        exact(raw,read(run/cohort/'results.json'))
    return result,sup


def replay(cohort,inputs,raw,checker,c):
    exact(raw['bindings'],shaped(inputs['bindings']));exact(raw['full_shape'],inputs['geometry'])
    p=raw['proof'];shape(p,raw['full_shape'])
    checked=shaped(checker.check(inputs['texts'],inputs['banned'],inputs['pool'],inputs['q'],inputs['seed'],inputs['alphabet'],inputs['denominator'],
        expected_source_hashes=inputs['source_hashes'],expected_old_banned=inputs['banned'],expected_old_certificate=inputs['parent_certificate'],
        expected_occurrence_sha256=c['parent50_arms'][cohort]['old_occurrence_order_sha256'],
        expected_base57_prefix_schedule=p['base57']['owner_prefix_schedule'],expected_price_prefix_schedule=p['price_prefix_schedule'],expected_count_streams=p['count_streams'],expected_price_caps=p['price_caps']))
    shape(checked,raw['full_shape'],'price_suffix_schedule')
    exact(diagnostics(p),diagnostics(checked))
    exact(scientific(p),scientific(checked));prior.independent_shape(p['base57'],checked['base57'],raw['full_shape'])
    assert checked['production_forward_schedule_sha256']==digest(p['price_prefix_schedule'])
    fake={**raw,'proof':p['base57']}
    prior.compare53(fake,inputs,checked['base57'],raw['full_shape'],c['parent53_arms'][cohort])
    basepublic=prior.prior.sanitize(cohort,inputs,{**raw,'proof':p['base57']['base']},checked['base57']['base'],raw['full_shape'])
    prior.prior.compare50(cohort,basepublic,checked['base57']['base']['lifted'],c['parent50_arms'][cohort])
    historical=c['parent57_arms'][cohort]
    assert digest(prior.scientific(checked['base57']))==historical['scientific_proof_sha256']
    assert digest(p['base57'])==historical['production_proof_sha256']
    assert digest(checked['base57']['owner_suffix_schedule'])==historical['independent_suffix_schedule_sha256']
    for key in ('rows','deltas_vs53'):exact(checked['base57'][key],historical[key])
    return checked


def positive(rows):return max((r['k'] for r in rows if r['integer_lower_bound'] is not None and r['integer_lower_bound']>0),default=None)

def context_row(row):
    fields=('k','charge','numerator','integer_lower_bound','one_owner_slots','shared_slots','empty_by_required_owners')
    assert set(row)==set(fields)
    return {key:row[key] for key in fields}

def summary(cohort,raw,checked,c):
    p=raw['proof'];base=p['base57'];tight=base['base']['tightened'];rows=p['rows'];deltas=p['deltas_vs57']
    return {'schema':'gamma.entry-price-path-cap.report-arm.v1','cohort':cohort,'complete':True,'validation_loaded':False,
        'contract_sha256':raw['contract_sha256'],'parent57_evidence_sha256':c['parent57_evidence']['sha256'],
        'source_identity_sha256':raw['bindings']['source_hashes_sha256'],'banned_set_sha256':raw['bindings']['bans_sha256'],
        'bindings_sha256':digest(raw['bindings']),'parent_certificate_sha256':c['parent57_arms'][cohort]['parent_certificate_sha256'],
        'geometry':raw['full_shape'],'class_counts':tight['class_counts'],'denominator':tight['denominator'],
        'path_numerator':sum(tight['path_numerators'].values()),'old_occurrences':tight['old_occurrences'],
        'baseline57_scientific_sha256':digest(prior.scientific(base)),'baseline53_paired_digests':base['base']['digests'],
        'production_proof_sha256':digest(p),'scientific_proof_sha256':digest(scientific(checked)),
        'digests':p['digests'],'independent_digests':checked['digests'],
        'rows':rows,'baseline57_rows':base['rows'],'deltas_vs57':deltas,
        'k3':{'row':rows[3],'delta':deltas[3]},'k256':{'row':rows[256],'delta':deltas[256]},
        'largest_positive_k':positive(rows),'baseline57_largest_positive_k':positive(base['rows']),
        'strict_charge_budgets':sum(d['charge_reduction']>0 for d in deltas),
        'strict_integer_budgets':sum(d['integer_bound_gain']>0 for d in deltas),
        'minimum_feasible_one_owner_budget':3,'positive_budgets_below_floor':[r['k'] for r in rows if r['k']<3 and r['integer_lower_bound']>0],
        'positive_budgets_in_feasible_classes':[r['k'] for r in rows if r['k']>=3 and r['integer_lower_bound']>0],
        'lambda_family':p['lambda_family'],'price_diagnostics':diagnostics(checked),
        'context61':{'k3':context_row(c['context61_arms'][cohort]['rows'][3]),
            'largest_positive_k':positive(c['context61_arms'][cohort]['rows']),
            'k256':context_row(c['context61_arms'][cohort]['rows'][256])},
        'production_work':p['work'],'report_work':checked['work'],'baseline57_production_work':base['work'],
        'baseline57_report_work':checked['base57']['work'],'baseline53_production_work':base['base']['work'],
        'baseline53_report_work':checked['base57']['base']['work'],
        'production_seconds':raw['seconds'],'production_peak_rss_kib':raw['peak_rss_kib'],
        'production_phase_seconds_sha256':digest(raw['phase_seconds']),
        'all257_independently_replayed':True,'all63_forward_recurrences_checked':True,'all57_forward_recurrences_checked':True,
        'historical57_reconstructed':True,'fresh_original_proof_replay':True,'shared_dependencies':SHARED}

ARM_FIELDS=set(('schema cohort complete validation_loaded contract_sha256 parent57_evidence_sha256 source_identity_sha256 banned_set_sha256 '
 'bindings_sha256 parent_certificate_sha256 geometry class_counts denominator path_numerator old_occurrences '
 'baseline57_scientific_sha256 baseline53_paired_digests production_proof_sha256 scientific_proof_sha256 digests independent_digests '
 'rows baseline57_rows deltas_vs57 k3 k256 largest_positive_k baseline57_largest_positive_k strict_charge_budgets strict_integer_budgets '
 'minimum_feasible_one_owner_budget positive_budgets_below_floor positive_budgets_in_feasible_classes lambda_family price_diagnostics context61 '
 'production_work report_work baseline57_production_work baseline57_report_work baseline53_production_work baseline53_report_work '
 'production_seconds production_peak_rss_kib production_phase_seconds_sha256 all257_independently_replayed all63_forward_recurrences_checked '
 'all57_forward_recurrences_checked historical57_reconstructed fresh_original_proof_replay shared_dependencies '
 'independent_receipt_sha256 production_arm_sha256 production_results_sha256 production_supervisor_sha256 report_worker_seconds report_peak_rss_kib').split())


def combine(run,output,c,elapsed,returncodes):
    number(elapsed,1200);exact(returncodes,[0,0]);run,output=Path(run),Path(output)
    assert not (output/'failure.json').exists();contract=sha(HERE/'contract.json');production,sup=accepted_production(run,c,contract);arms=[]
    for cohort,raw in zip(COHORTS,production['arms']):
        assert not (output/(cohort+'-failure.json')).exists()
        checked=read(output/(cohort+'-proof.json'));a=read(output/(cohort+'.json'));assert set(a)==ARM_FIELDS
        shape(checked,raw['full_shape'],'price_suffix_schedule');exact(scientific(raw['proof']),scientific(checked))
        prior.independent_shape(raw['proof']['base57'],checked['base57'],raw['full_shape'])
        assert checked['production_forward_schedule_sha256']==digest(raw['proof']['price_prefix_schedule'])
        for key,value in summary(cohort,raw,checked,c).items():exact(a[key],value)
        for key,path in (('independent_receipt_sha256',output/(cohort+'-proof.json')),('production_arm_sha256',run/cohort/'results.json'),
            ('production_results_sha256',run/'results.json'),('production_supervisor_sha256',run/'supervisor.json')):assert a[key]==sha(path)
        number(a['report_worker_seconds'],min(600,elapsed));integer(a['report_peak_rss_kib'],1,ADDRESS_SPACE_BYTES//1024);arms.append(a)
    rank=lambda k:-1 if k is None else k
    predictions={'P1':True,'P2':any(a['k3']['delta']['charge_reduction']>0 for a in arms),
        'P3':any(rank(a['largest_positive_k'])>rank(a['baseline57_largest_positive_k']) for a in arms),
        'P4':any(a['k256']['delta']['charge_reduction']>0 for a in arms),'P5':any(a['k256']['row']['integer_lower_bound']>0 for a in arms)}
    return {'schema':'gamma.entry-price-path-cap.report.v1','complete':True,'validation_loaded':False,'contract_sha256':contract,
        'arms':arms,'predictions':predictions,'population':'fixed300_fit_only','parent57_evidence_sha256':c['parent57_evidence']['sha256'],
        'context61_evidence_sha256':c['context61_evidence']['sha256'],'context61_descriptive_only':True,
        'feasibility59_sha256':c['feasibility59']['sha256'],'production_results_sha256':sha(run/'results.json'),
        'production_supervisor_sha256':sha(run/'supervisor.json'),'production_seconds':production['seconds'],'report_seconds':elapsed,
        'validation_or_cases_opened':False,'fresh_original_proof_replay':True,'private_input_files':9,
        'required_owner_constraint_applied':False,'new_qualification_jobs':0,'new_packets':0,
        'qualification':'Exact original13 source reuse; unchanged-source23 exit137 separate.',
        'coverage_scope':'Item59 existing-seed proof establishes minimum feasible at-most budget3; numerical k<3 bounds are vacuous.',
        'm1_claim':False,'promotion_allowed':False,'current_best_changed':False,'shared_dependencies':SHARED}


def failure_result(error):
    return {'schema':'gamma.entry-price-path-cap.report.v1','complete':False,'validation_loaded':False,'verdicts':None,
        'failure_type':type(error).__name__,'predictions':dict.fromkeys(('P1','P2','P3','P4','P5')),'promotion_allowed':False}


def markdown(result):
    if result['complete'] is not True:return '# Item63 incomplete\n\nNo verdict. Incomplete execution or replay.\n'
    lines=['# Item63 fixed entry prices','','Fresh57/53/50 reconstruction, fixed15 prices and every forward recurrence. Item61 is descriptive only.','',
        '| Cohort | 57 k3 | 63 k3 | 57 k* | 63 k* | 57 k256 | 63 k256 | 61 k3 (context) | 61 k* (context) |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for a in result['arms']:
        lines.append(f"| {a['cohort']} | {a['baseline57_rows'][3]['integer_lower_bound']} | {a['k3']['row']['integer_lower_bound']} | {a['baseline57_largest_positive_k']} | {a['largest_positive_k']} | {a['baseline57_rows'][256]['integer_lower_bound']} | {a['k256']['row']['integer_lower_bound']} | {a['context61']['k3']['integer_lower_bound']} | {a['context61']['largest_positive_k']} |")
    lines+=['','All257 paired rows, raw/ceiling gains and aggregate price diagnostics are in results.json. k* is the largest positive k. Item59 establishes minimum feasible at-most budget3; positive k<3 bounds are coverage-vacuous. Nonpositive is inconclusive.',
        '', 'Diagnostics count positive-original-weight finite ranks, whether allocated or not. Smallest minimizing price index breaks ties. A maximum-grid minimizer does not establish benefit from a larger price; absence does not establish adequacy.',
        '', 'No new witness, qualification, M1, validation or current-best claim. Original13 qualification reused; unchanged-source23 exit137 remains separate.',
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
        checker = module('entry63_independent_worker', HERE/'independent.py')
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
