"""Fresh joint-cap replay; original nine inputs only after accepted production."""
import signal
import time
class HardDeadline(BaseException):pass
def _expired(*_):raise HardDeadline('independent report deadline')
BOOT_STARTED=time.monotonic() if __name__=='__main__' else None
if BOOT_STARTED is not None:
    signal.signal(signal.SIGALRM,_expired);signal.setitimer(signal.ITIMER_REAL,600)
import argparse
import importlib.util
import json
import os
from pathlib import Path
import resource
import binding as b
HERE=b.HERE;COHORTS=('R','naming');WORKER_SECONDS=600;PHASE_SECONDS=1200;ADDRESS_SPACE_BYTES=8*1024**3

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
prior=module('joint60_report57',HERE.parent/'owner-path-cap-v1/report.py')
exact=prior.exact;shaped=prior.shaped;digest=prior.digest;integer=prior.integer;number=prior.number
sha=b.sha;read=b.read;write=b.write;config_limits=prior.config_limits
COMMON=('local_shared_top_entries','local_shared_prefixes','local_shared_counts','all_caps','split_rows','rows','deltas_vs57')
PROD_WORK=('baseline57_reconstructions','additional53_contexts','old_occurrences_inspected','local_shared_occurrence_contributions',
 'zero_identity_inspections','max_local_accumulator_entries','retained_local_shared_entries','schedule_endpoints_inspected',
 'schedule_occurrences_admitted','allocation_heap_offers','allocation_heap_pops')
AUDIT_WORK=('old_occurrences_replayed','old_bellman_edges_checked','support_suffix_positions_checked','support_groups_classified',
 'shared_occurrences_aggregated','shared_entries_reconciled','local_shared_entries_sorted','schedule_endpoints_inspected',
 'schedule_occurrences_admitted','production_forward_positions_checked','production_forward_endpoints_inspected',
 'allocation_owner_scans','allocation_candidates_compared','allocation_increments_checked')
SHARED='Original source/parser and item33 Index; unchanged57 production/independent baselines and53 potential contexts. Independent AC/local sort, backward schedules, recurrence checks and owner-scan allocation.'


def scientific(proof):
    return {'schema':proof['schema'],'base57':prior.scientific(proof['base57']),**{key:proof[key] for key in COMMON}}


def shape(proof,geometry,direction='all_prefix_schedule'):
    isprod=direction=='all_prefix_schedule'
    extras=set() if isprod else {'production_forward_schedule_checked','production_forward_schedule_sha256','shared_dependency','scalar_replay'}
    assert set(proof)=={'schema','base57','digests','work',direction,*COMMON}|extras
    assert proof['schema']=='gamma.joint-path-cap.supplied.v1'
    base=proof['base57'];ids=set(base['owner_caps'])
    if isprod:prior.owner_shape(base,geometry)
    D=base['base']['tightened']['denominator'];L=sum(base['base']['tightened']['path_numerators'].values())
    m=base['base']['tightened']['class_counts']['2'];positions=endpoints=0
    for key in ('local_shared_top_entries','local_shared_prefixes','local_shared_counts','all_caps',direction):assert set(proof[key])==ids
    for pid in sorted(ids):
        entries=proof['local_shared_top_entries'][pid];assert type(entries) is list and len(entries)==min(256,m)
        for e in entries:
            assert type(e) is list and len(e)==3
            integer(e[0],0);integer(e[1],0,geometry['full_groups']-1);integer(e[2],1)
        assert entries==sorted(entries,key=lambda e:(-e[0],e[1],e[2])) and len({tuple(e[1:]) for e in entries})==len(entries)
        counts=proof['local_shared_counts'][pid];assert set(counts)=={'available','occurring','positive'}
        for v in counts.values():integer(v,0,m)
        assert counts['available']==m and counts['positive']<=counts['occurring']
        prefix=[0]
        for w,_,_ in entries:prefix.append(prefix[-1]+w)
        exact(prefix,proof['local_shared_prefixes'][pid]);cap=integer(proof['all_caps'][pid],base['owner_caps'][pid])
        vec=proof[direction][pid];assert type(vec) is list and len(vec)>1
        for v in vec:integer(v,0)
        assert vec[0 if isprod else -1]==0 and vec[-1 if isprod else 0]==cap
        assert vec==sorted(vec,reverse=not isprod)
        n=len(vec)-1;positions+=n;endpoints+=n*(n+1)//2
    assert positions==geometry['source_characters']
    splits=proof['split_rows'];assert len(splits)==len(base['one_owner_prefix'])
    for j,s in enumerate(splits):
        assert set(s)=={'one_owner_slots','shared_slots','shared_slots_available','baseline','joint_charge','prior57_charge','charge','allocation_choices'}
        for k,v in s.items():
            if k!='allocation_choices':integer(v,0)
        assert s['one_owner_slots']==j and s['shared_slots']==256-j
        available=min(256-j,len(base['shared_prefix'])-1);assert s['shared_slots_available']==available
        local={pid:proof['local_shared_prefixes'][pid][min(256-j,len(proof['local_shared_prefixes'][pid])-1)] for pid in ids}
        baseline=sum(min(local[pid],proof['all_caps'][pid]) for pid in ids);assert s['baseline']==baseline
        counts=dict.fromkeys(ids,0);total=baseline
        assert len(s['allocation_choices'])==j
        for choice in s['allocation_choices']:
            assert type(choice) is list and len(choice)==3
            pid,rank,value=choice;assert pid in ids;integer(rank,1);integer(value,0)
            assert rank==counts[pid]+1 and rank<len(base['owner_prefixes'][pid]);counts[pid]=rank
            vals=base['owner_prefixes'][pid];cap=proof['all_caps'][pid]
            assert value==min(local[pid]+vals[rank],cap)-min(local[pid]+vals[rank-1],cap);total+=value
        assert s['joint_charge']==total and s['prior57_charge']==base['shared_prefix'][available]+base['one_owner_prefix'][j]
        assert s['charge']==min(total,s['prior57_charge'])
    assert len(proof['rows'])==len(proof['deltas_vs57'])==257
    best=None
    for k,(row,old,delta) in enumerate(zip(proof['rows'],base['rows'],proof['deltas_vs57'])):
        if k<len(splits) and (best is None or splits[k]['charge']>best['charge']):best=splits[k]
        charge=best['charge'];num=L-charge
        exact(row,{'k':k,'charge':charge,'one_owner_slots':best['one_owner_slots'],'shared_slots':best['shared_slots_available'],
                   'numerator':num,'integer_lower_bound':-(-num//D)})
        exact(delta,{'k':k,'charge_reduction':old['charge']-charge,'integer_bound_gain':row['integer_lower_bound']-old['integer_lower_bound']})
        assert delta['charge_reduction']>=0
    assert set(proof['digests'])=={key+'_sha256' for key in (*COMMON,direction)}|{'base57_sha256'}
    for key in (*COMMON,direction):assert proof['digests'][key+'_sha256']==digest(proof[key])
    assert proof['digests']['base57_sha256']==digest(prior.scientific(base))
    assert set(proof['work'])==set(PROD_WORK if isprod else AUDIT_WORK)
    for v in proof['work'].values():integer(v,0)
    assert proof['work']['schedule_endpoints_inspected']==endpoints
    assert proof['work']['schedule_occurrences_admitted']==endpoints-geometry['exact_ban_occurrences']
    if isprod:
        w=proof['work'];assert w['baseline57_reconstructions']==w['additional53_contexts']==1
        assert w['old_occurrences_inspected']==base['base']['tightened']['old_occurrences']
        assert w['retained_local_shared_entries']==sum(map(len,proof['local_shared_top_entries'].values()))
        assert w['max_local_accumulator_entries']==max((c['occurring'] for c in proof['local_shared_counts'].values()),default=0)
        assert w['allocation_heap_pops']==sum(range(len(splits)))
        offers=len(splits)*sum(len(v)>1 for v in base['owner_prefixes'].values())
        offers+=sum(rank+1<len(base['owner_prefixes'][pid]) for split in splits for pid,rank,_ in split['allocation_choices'])
        assert w['allocation_heap_offers']==offers
    else:
        assert proof['production_forward_schedule_checked'] is True
        assert proof['work']['production_forward_positions_checked']==positions
        assert proof['work']['production_forward_endpoints_inspected']==endpoints


def accepted_production(run,c,contract):
    config_limits(c);b.verify_parent50(c);b.verify_parent53(c);b.verify_parent57(c);b.verify_feasibility(c)
    run=Path(run);assert not (run/'failure.json').exists()
    result,sup=read(run/'results.json'),read(run/'supervisor.json')
    assert result['complete'] is sup['complete'] is True and result['validation_loaded'] is False
    assert sup['phase']=='production' and result['contract_sha256']==sup['contract_sha256']==contract
    exact(sup['returncodes'],[0,0]);number(sup['elapsed'],1200);number(sup['cleanup_seconds'],10);number(result['seconds'],sup['elapsed'])
    assert [a['cohort'] for a in result['arms']]==list(COHORTS)
    for raw in result['arms']:
        cohort=raw['cohort'];assert not (run/cohort/'failure.json').exists() and not (run/(cohort+'-failure.json')).exists()
        assert set(raw)=={'schema','cohort','complete','validation_loaded','contract_sha256','bindings','full_shape','proof','phase_seconds','seconds','peak_rss_kib'}
        assert raw['schema']=='gamma.joint-path-cap.arm.v1' and raw['complete'] is True and raw['validation_loaded'] is False
        assert raw['contract_sha256']==contract;number(raw['seconds'],min(600,result['seconds']));integer(raw['peak_rss_kib'],1,ADDRESS_SPACE_BYTES//1024)
        assert set(raw['phase_seconds'])=={'input','proof'}
        for v in raw['phase_seconds'].values():number(v,raw['seconds'])
        assert sum(raw['phase_seconds'].values())<=raw['seconds']
        exact(raw['full_shape'],c['full_shape'][cohort]);shape(raw['proof'],raw['full_shape'])
        assert set(raw['proof']['base57']['owner_caps'])==set(map(str,c['fit_ids']))
        exact(raw,read(run/cohort/'results.json'))
    return result,sup


def replay(cohort,inputs,raw,checker,c):
    exact(raw['bindings'],shaped(inputs['bindings']));exact(raw['full_shape'],inputs['geometry'])
    p=raw['proof'];shape(p,raw['full_shape'])
    checked=shaped(checker.check(inputs['texts'],inputs['banned'],inputs['pool'],inputs['q'],inputs['seed'],inputs['alphabet'],inputs['denominator'],
        expected_source_hashes=inputs['source_hashes'],expected_old_banned=inputs['banned'],expected_old_certificate=inputs['parent_certificate'],
        expected_occurrence_sha256=c['parent50_arms'][cohort]['old_occurrence_order_sha256'],
        expected_base57_prefix_schedule=p['base57']['owner_prefix_schedule'],expected_prefix_schedule=p['all_prefix_schedule']))
    shape(checked,raw['full_shape'],'all_suffix_schedule')
    exact(p['work']['local_shared_occurrence_contributions'],checked['work']['shared_occurrences_aggregated'])
    exact(scientific(p),scientific(checked));prior.independent_shape(p['base57'],checked['base57'],raw['full_shape'])
    assert checked['production_forward_schedule_sha256']==digest(p['all_prefix_schedule'])
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


def positive(rows):return max((r['k'] for r in rows if r['integer_lower_bound']>0),default=None)

def summary(cohort,raw,checked,c):
    p=raw['proof'];base=p['base57'];tight=base['base']['tightened'];rows=p['rows'];deltas=p['deltas_vs57']
    return {'schema':'gamma.joint-path-cap.report-arm.v1','cohort':cohort,'complete':True,'validation_loaded':False,
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
        'local_shared_aggregates':{'owners':len(p['all_caps']),'all_cap_sum':sum(p['all_caps'].values()),
            'all_cap_max':max(p['all_caps'].values(),default=0),'retained_local_entries':sum(map(len,p['local_shared_top_entries'].values())),
            'local_occurring_entries':sum(v['occurring'] for v in p['local_shared_counts'].values()),
            'local_positive_entries':sum(v['positive'] for v in p['local_shared_counts'].values())},
        'production_work':p['work'],'report_work':checked['work'],'baseline57_production_work':base['work'],
        'baseline57_report_work':checked['base57']['work'],'baseline53_production_work':base['base']['work'],
        'baseline53_report_work':checked['base57']['base']['work'],
        'production_seconds':raw['seconds'],'production_peak_rss_kib':raw['peak_rss_kib'],
        'production_phase_seconds_sha256':digest(raw['phase_seconds']),
        'all257_independently_replayed':True,'all60_forward_recurrences_checked':True,'all57_forward_recurrences_checked':True,
        'historical57_reconstructed':True,'fresh_original_proof_replay':True,'shared_dependencies':SHARED}

ARM_FIELDS=set(('schema cohort complete validation_loaded contract_sha256 parent57_evidence_sha256 source_identity_sha256 banned_set_sha256 '
 'bindings_sha256 parent_certificate_sha256 geometry class_counts denominator path_numerator old_occurrences '
 'baseline57_scientific_sha256 baseline53_paired_digests production_proof_sha256 scientific_proof_sha256 digests independent_digests '
 'rows baseline57_rows deltas_vs57 k3 k256 largest_positive_k baseline57_largest_positive_k strict_charge_budgets strict_integer_budgets '
 'minimum_feasible_one_owner_budget positive_budgets_below_floor positive_budgets_in_feasible_classes local_shared_aggregates '
 'production_work report_work baseline57_production_work baseline57_report_work baseline53_production_work baseline53_report_work '
 'production_seconds production_peak_rss_kib production_phase_seconds_sha256 all257_independently_replayed all60_forward_recurrences_checked '
 'all57_forward_recurrences_checked historical57_reconstructed fresh_original_proof_replay shared_dependencies '
 'independent_receipt_sha256 production_arm_sha256 production_results_sha256 production_supervisor_sha256 report_worker_seconds report_peak_rss_kib').split())


def combine(run,output,c,elapsed,returncodes):
    number(elapsed,1200);exact(returncodes,[0,0]);run,output=Path(run),Path(output)
    assert not (output/'failure.json').exists();contract=sha(HERE/'contract.json');production,sup=accepted_production(run,c,contract);arms=[]
    for cohort,raw in zip(COHORTS,production['arms']):
        assert not (output/(cohort+'-failure.json')).exists()
        checked=read(output/(cohort+'-proof.json'));a=read(output/(cohort+'.json'));assert set(a)==ARM_FIELDS
        shape(checked,raw['full_shape'],'all_suffix_schedule');exact(scientific(raw['proof']),scientific(checked))
        prior.independent_shape(raw['proof']['base57'],checked['base57'],raw['full_shape'])
        assert checked['production_forward_schedule_sha256']==digest(raw['proof']['all_prefix_schedule'])
        for key,value in summary(cohort,raw,checked,c).items():exact(a[key],value)
        for key,path in (('independent_receipt_sha256',output/(cohort+'-proof.json')),('production_arm_sha256',run/cohort/'results.json'),
            ('production_results_sha256',run/'results.json'),('production_supervisor_sha256',run/'supervisor.json')):assert a[key]==sha(path)
        number(a['report_worker_seconds'],min(600,elapsed));integer(a['report_peak_rss_kib'],1,ADDRESS_SPACE_BYTES//1024);arms.append(a)
    rank=lambda k:-1 if k is None else k
    predictions={'P1':True,'P2':any(a['k3']['delta']['charge_reduction']>0 for a in arms),
        'P3':any(rank(a['largest_positive_k'])>rank(a['baseline57_largest_positive_k']) for a in arms),
        'P4':any(a['k256']['delta']['charge_reduction']>0 for a in arms),'P5':any(a['k256']['row']['integer_lower_bound']>0 for a in arms)}
    return {'schema':'gamma.joint-path-cap.report.v1','complete':True,'validation_loaded':False,'contract_sha256':contract,
        'arms':arms,'predictions':predictions,'population':'fixed300_fit_only','parent57_evidence_sha256':c['parent57_evidence']['sha256'],
        'feasibility59_sha256':c['feasibility59']['sha256'],'production_results_sha256':sha(run/'results.json'),
        'production_supervisor_sha256':sha(run/'supervisor.json'),'production_seconds':production['seconds'],'report_seconds':elapsed,
        'validation_or_cases_opened':False,'fresh_original_proof_replay':True,'private_input_files':9,
        'required_owner_constraint_applied':False,'new_qualification_jobs':0,'new_packets':0,
        'qualification':'Exact original13 source reuse; unchanged-source23 exit137 separate.',
        'coverage_scope':'Item59 existing-seed proof establishes minimum feasible at-most budget3; numerical k<3 bounds are vacuous.',
        'm1_claim':False,'promotion_allowed':False,'current_best_changed':False,'shared_dependencies':SHARED}


def failure_result(error):
    return {'schema':'gamma.joint-path-cap.report.v1','complete':False,'validation_loaded':False,'verdicts':None,
        'failure_type':type(error).__name__,'predictions':dict.fromkeys(('P1','P2','P3','P4','P5')),'promotion_allowed':False}


def markdown(result):
    if result['complete'] is not True:return '# Item60 incomplete\n\nNo verdict. Incomplete execution or replay.\n'
    lines=['# Item60 joint path caps','','Fresh57/53/50 reconstruction; local shared weights and all-arc schedules; no required-owner constraint.','',
        '| Cohort | k3 bound | k256 bound | Largest positive k,57 to60 | Raw / integer strict budgets |',
        '| --- | ---: | ---: | --- | ---: |']
    for a in result['arms']:lines.append(f"| {a['cohort']} | {a['k3']['row']['integer_lower_bound']} | {a['k256']['row']['integer_lower_bound']} | {a['baseline57_largest_positive_k']} to {a['largest_positive_k']} | {a['strict_charge_budgets']} / {a['strict_integer_budgets']} |")
    lines+=['','All257 paired rows and raw/ceiling gains are retained in results.json. Item59 establishes minimum feasible at-most budget3; positive k<3 values are vacuous. Nonpositive is inconclusive. No new witness, qualification, M1 or current-best claim.',
        '', 'Predictions: '+json.dumps(result['predictions'],sort_keys=True),'','Original13 qualification reused; unchanged-source23 exit137 remains separate.']
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
        checker = module('joint60_independent_worker', HERE/'independent.py')
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
