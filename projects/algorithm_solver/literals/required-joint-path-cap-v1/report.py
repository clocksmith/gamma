"""Fresh required-owner replay with explicitly inherited item60 scientific proof."""
import signal
import time
class HardDeadline(BaseException):pass
def _expired(*_):raise HardDeadline('independent report deadline')
BOOT_STARTED=time.monotonic() if __name__=='__main__' else None
if BOOT_STARTED is not None:
    signal.signal(signal.SIGALRM,_expired);signal.setitimer(signal.ITIMER_REAL,600)
import argparse
import json
import os
from pathlib import Path
import resource
import binding as b
import parent_receipts as pr
import allocation
HERE=b.HERE;WORKER_SECONDS=600;PHASE_SECONDS=1200;ADDRESS_SPACE_BYTES=8*1024**3;COHORTS=b.COHORTS
read=b.read;write=b.write;sha=b.sha;digest=b.digest;exact=b.exact;integer=b.integer;number=b.number
INHERITANCE={'fresh_item60_full_graph_replay':False,'fresh_forced_owner_replay':True,'fresh_constrained_allocation_replay':True}
EXTRA_FIELDS={'report_worker_seconds','report_peak_rss_kib','production_arm_sha256','production_results_sha256','production_supervisor_sha256','independent_receipt_sha256'}

def config_limits(c):
    assert c['active'] is True;exact(c['limits'],b.LIMITS)
    assert len(c['fit_ids'])==len(set(c['fit_ids']))==300
    for pid in c['fit_ids']:integer(pid)


def receipt_reads(rows,c,cohort,role):
    assert type(rows) is list and len(rows)==3
    expected={rel:c['role_private_files'][role][rel] for rel in (b.SOURCES[cohort],b.POOLS[cohort],b.PARENTS[role][cohort])}
    assert {row['path'] for row in rows}==set(expected)
    for row in rows:
        assert set(row)=={'path','sha256','bytes'} and row['sha256']==expected[row['path']]
        integer(row['bytes'],1,b.MAX_BYTES)


def accepted_production(run,c,contract_hash):
    config_limits(c);b.public_inputs(c);run=Path(run)
    assert not (run/'failure.json').exists()
    production,supervisor=read(run/'results.json'),read(run/'supervisor.json')
    assert production['complete'] is supervisor['complete'] is True and production['validation_loaded'] is False
    assert supervisor['phase']=='production' and production['contract_sha256']==supervisor['contract_sha256']==contract_hash
    exact(supervisor['returncodes'],[0,0]);number(supervisor['elapsed'],1200);number(supervisor['cleanup_seconds'],10)
    number(production['seconds'],supervisor['elapsed'])
    assert [a['cohort'] for a in production['arms']]==list(COHORTS)
    for raw in production['arms']:
        cohort=raw['cohort'];assert not (run/cohort/'failure.json').exists() and not (run/(cohort+'-failure.json')).exists()
        assert set(raw)=={'schema','cohort','complete','validation_loaded','contract_sha256','read_receipts','proof','phase_seconds','seconds','peak_rss_kib'}
        assert raw['schema']=='gamma.required-joint-path-cap.arm.v1' and raw['complete'] is True and raw['validation_loaded'] is False
        assert raw['contract_sha256']==contract_hash
        number(raw['seconds'],min(600,production['seconds']));integer(raw['peak_rss_kib'],1,ADDRESS_SPACE_BYTES//1024)
        assert set(raw['phase_seconds'])=={'input','proof'}
        for v in raw['phase_seconds'].values():number(v,raw['seconds'])
        assert sum(raw['phase_seconds'].values())<=raw['seconds']
        receipt_reads(raw['read_receipts'],c,cohort,'production')
        assert set(raw['proof'])=={'coverage','allocation','parent_scientific_proof_sha256','source_identity_sha256','banned_set_sha256'}
        b.coverage_report().proof_shape(raw['proof']['coverage'],c['parent50_arms'][cohort],set(map(str,c['fit_ids'])))
        public=c['parent60_arms'][cohort]
        for field,authority in (('parent_scientific_proof_sha256','scientific_proof_sha256'),
            ('source_identity_sha256','source_identity_sha256'),('banned_set_sha256','banned_set_sha256')):
            exact(raw['proof'][field],public[authority])
        allocation_shape(raw['proof']['allocation'],c,cohort,'heap')
        exact(read(run/cohort/'results.json'),raw)
    return production,supervisor


def allocation_shape(result,c,cohort,method=None):
    assert set(result)=={'schema','coverage_floor','owner57_prefix','owner61_prefix','owner57_choices','owner61_choices',
        'split_rows','parent60_rows','parent61_rows','rows','digests','work'}
    assert result['schema']=='gamma.required-joint-path-cap.allocation.v1'
    integer(result['coverage_floor'],3,3);pr.parents_rebuilt(result,c,cohort)
    fields={'k','empty_by_required_owners','one_owner_slots','shared_slots','charge','numerator','integer_lower_bound',
        'charge_reduction_vs60','charge_reduction_vs61','integer_gain_vs60','integer_gain_vs61'}
    expected=c['parent60_arms'][cohort];L=expected['path_numerator'];D=expected['denominator']
    for k,row in enumerate(result['rows']):
        assert set(row)==fields;exact(row['k'],k);exact(row['empty_by_required_owners'],k<3)
        if k<3:assert all(v is None for key,v in row.items() if key not in ('k','empty_by_required_owners'))
        else:
            for key in ('one_owner_slots','shared_slots','charge','charge_reduction_vs60','charge_reduction_vs61','integer_gain_vs60','integer_gain_vs61'):integer(row[key])
            for key in ('numerator','integer_lower_bound'):assert type(row[key]) is int
            assert 3<=row['one_owner_slots']<=k and row['one_owner_slots']+row['shared_slots']<=256
            assert row['numerator']==L-row['charge'] and row['integer_lower_bound']==-(-row['numerator']//D)
            for n in ('60','61'):
                old=c['parent'+n+'_arms'][cohort]['rows'][k]
                assert row['charge_reduction_vs'+n]==old['charge']-row['charge']
                assert row['integer_gain_vs'+n]==row['integer_lower_bound']-old['integer_lower_bound']
    assert all(a['charge']<=z['charge'] for a,z in zip(result['rows'][3:],result['rows'][4:]))
    keys=('owner57_prefix','owner61_prefix','owner57_choices','owner61_choices','split_rows','parent60_rows','parent61_rows','rows')
    assert set(result['digests'])=={key+'_sha256' for key in keys}
    for key in keys:assert result['digests'][key+'_sha256']==digest(result[key])
    assert set(result['work'])=={'heap_offers','heap_pops','owner_scan_visits','joint_splits'}
    for value in result['work'].values():integer(value)
    if method=='heap':assert result['work']['owner_scan_visits']==0
    if method=='scan':assert result['work']['heap_offers']==result['work']['heap_pops']==0
    splitfields={'one_owner_slots','shared_slots','shared_slots_available','zero_baseline','mandatory_baseline','mandatory_increment',
        'joint60_charge','prior57_charge','charge60','joint62_charge','charge61','charge62','unconstrained_choices','required_choices'}
    for j,row in enumerate(result['split_rows']):
        assert set(row)==splitfields and row['one_owner_slots']==j
        for key,value in row.items():
            if key in ('unconstrained_choices','required_choices'):assert type(value) is list
            elif value is None:assert j<3 and key in ('mandatory_baseline','mandatory_increment','joint62_charge','charge61','charge62')
            else:integer(value)
    assert result['work']['joint_splits']==len(result['split_rows'])


def replay(cohort,inputs,raw,c):
    expected=c['parent60_arms'][cohort]
    parent=pr.validate(inputs['parent'],'report',expected,c['parent57_arms'][cohort],c['public_files'][b.PUBLIC['60contract']],set(inputs['texts']))
    assert raw['proof']['parent_scientific_proof_sha256']==parent['scientific_proof_sha256']
    assert raw['proof']['source_identity_sha256']==digest(inputs['source_hashes'])==expected['source_identity_sha256']
    assert raw['proof']['banned_set_sha256']==digest(sorted(inputs['banned']))==expected['banned_set_sha256']
    original=raw['proof']['coverage'];pr.coverage_check(original,inputs,c,cohort,'prefix_reachable')
    checked=b.coverage().replay(inputs['texts'],inputs['pool'],inputs['banned'])
    forced=pr.coverage_check(checked,inputs,c,cohort,'suffix_reachable')
    for key in b.coverage_report().COMMON_FIELDS:exact(original[key],checked[key])
    b.coverage_report().check_vectors(inputs['texts'],inputs['pool'],original,checked)
    result=pr.normalized(allocation.scan(**pr.allocation_inputs(parent,forced)))
    allocation_shape(raw['proof']['allocation'],c,cohort,'heap');allocation_shape(result,c,cohort,'scan')
    exact(pr.allocation_science(raw['proof']['allocation']),pr.allocation_science(result))
    receipt_reads(inputs['reads'],c,cohort,'report')
    return {'coverage':checked,'allocation':result,'parent_scientific_proof_sha256':parent['scientific_proof_sha256'],
            'ancestral_reads':inputs['reads'],'all_forward_recurrences_checked':True}


def positive(rows):return max((r['k'] for r in rows if r['integer_lower_bound'] is not None and r['integer_lower_bound']>0),default=None)


SPLIT_PUBLIC=('one_owner_slots','shared_slots','shared_slots_available','zero_baseline','mandatory_baseline',
    'mandatory_increment','joint60_charge','prior57_charge','charge60','joint62_charge','charge61','charge62')


def summary(cohort,raw,checked,c):
    expected=c['parent60_arms'][cohort];cov=checked['coverage'];result=checked['allocation']
    allocation_shape(result,c,cohort,'scan');rows=result['rows']
    curves={n:c['parent'+n+'_arms'][cohort]['rows'] for n in ('57','60','61')};curves['62']=rows
    comparison={n:{'k3':curve[3],'largest_positive_k':positive(curve),'k256':curve[256]} for n,curve in curves.items()}
    splits=[{key:row[key] for key in SPLIT_PUBLIC} for row in result['split_rows']]
    defined=[row for row in splits if row['one_owner_slots']>=3]
    split_counts={'defined_splits':len(defined),
        'joint60_less_than_prior57':sum(row['joint60_charge']<row['prior57_charge'] for row in defined),
        'joint62_less_than_required61':sum(row['joint62_charge']<row['charge61'] for row in defined),
        'split62_strict_vs61':sum(row['charge62']<row['charge61'] for row in defined),
        'split62_strict_vs60':sum(row['charge62']<row['charge60'] for row in defined)}
    return {'schema':'gamma.required-joint-path-cap.report-arm.v1','cohort':cohort,'complete':True,'validation_loaded':False,
        'contract_sha256':raw['contract_sha256'],
        **{'parent'+n+'_evidence_sha256':c['public_files'][b.PUBLIC[n]] for n in ('56','57','60','61')},
        'feasibility59_sha256':c['public_files'][b.PUBLIC['59']],
        'parent_scientific_proof_sha256':expected['scientific_proof_sha256'],
        'source_identity_sha256':expected['source_identity_sha256'],'banned_set_sha256':expected['banned_set_sha256'],
        'coverage_floor':len(cov['forced_source_ids']),'forced_source_ids_sha256':digest(cov['forced_source_ids']),
        'source_success_sha256':digest(cov['source_success']),'owner_classes_sha256':digest(cov['owner_classes']),
        'production_prefix_sha256':digest(raw['proof']['coverage']['prefix_reachable']),
        'independent_suffix_sha256':digest(cov['suffix_reachable']),
        'inherited_local_shared_prefixes_sha256':expected['digests']['local_shared_prefixes_sha256'],
        'inherited_all_caps_sha256':expected['digests']['all_caps_sha256'],
        'inherited_capped_prefixes_sha256':c['parent57_arms'][cohort]['capped_prefixes_sha256'],
        'inherited_owner_prefixes_sha256':c['parent57_arms'][cohort]['owner_prefixes_sha256'],
        'coverage_occurrences':cov['occurrences'],'coverage_occurrence_sha256':cov['occurrence_sha256'],
        'denominator':expected['denominator'],'path_numerator':expected['path_numerator'],
        'allocation_sha256':digest(pr.allocation_science(result)),'allocation_digests':result['digests'],
        'production_allocation_work':raw['proof']['allocation']['work'],'independent_allocation_work':result['work'],
        'rows':rows,'curves':curves,'comparison':comparison,'split_rows':splits,'split_counts':split_counts,
        'largest_positive_k':positive(rows),'naming_largest_positive_exceeds4':None if cohort!='naming' else positive(rows) is not None and positive(rows)>4,
        'strict_charge_budgets':{n:sum(row['charge_reduction_vs'+n] is not None and row['charge_reduction_vs'+n]>0 for row in rows) for n in ('60','61')},
        'strict_integer_budgets':{n:sum(row['integer_gain_vs'+n] is not None and row['integer_gain_vs'+n]>0 for row in rows) for n in ('60','61')},
        'empty_budgets':[row['k'] for row in rows if row['empty_by_required_owners']],
        'minimum_feasible_one_owner_budget':c['parent59_arms'][cohort]['minimum_feasible_one_owner_budget'],
        'production_seconds':raw['seconds'],'production_peak_rss_kib':raw['peak_rss_kib'],
        'production_phase_seconds_sha256':digest(raw['phase_seconds']),
        'ancestral_reads_sha256':digest(checked['ancestral_reads']),
        'inherited_scientific_authority':'Accepted60 raw/independent receipts and public commitments; no new full-graph replay.',
        **INHERITANCE,'all_forward_recurrences_checked':True,'all257_rows_replayed':True}


def combine(run,output,c,elapsed,returncodes):
    number(elapsed,1200);exact(returncodes,[0,0]);run,output=Path(run),Path(output)
    assert not (output/'failure.json').exists();contract=sha(HERE/'contract.json')
    production,supervisor=accepted_production(run,c,contract);arms=[]
    for cohort,raw in zip(COHORTS,production['arms']):
        assert not (output/(cohort+'-failure.json')).exists()
        checked=read(output/(cohort+'-proof.json'));a=read(output/(cohort+'.json'))
        assert set(checked)=={'coverage','allocation','parent_scientific_proof_sha256','ancestral_reads','all_forward_recurrences_checked'}
        assert checked['all_forward_recurrences_checked'] is True
        assert checked['parent_scientific_proof_sha256']==c['parent60_arms'][cohort]['scientific_proof_sha256']
        b.coverage_report().proof_shape(checked['coverage'],c['parent50_arms'][cohort],set(map(str,c['fit_ids'])),'suffix_reachable')
        for key in b.coverage_report().COMMON_FIELDS:exact(raw['proof']['coverage'][key],checked['coverage'][key])
        exact(pr.allocation_science(raw['proof']['allocation']),pr.allocation_science(checked['allocation']));receipt_reads(checked['ancestral_reads'],c,cohort,'report')
        expected=summary(cohort,raw,checked,c)
        assert set(a)==set(expected)|EXTRA_FIELDS
        for key,value in expected.items():exact(a[key],value)
        for key,path in (('independent_receipt_sha256',output/(cohort+'-proof.json')),
            ('production_arm_sha256',run/cohort/'results.json'),('production_results_sha256',run/'results.json'),
            ('production_supervisor_sha256',run/'supervisor.json')):assert a[key]==sha(path)
        number(a['report_worker_seconds'],min(600,elapsed));integer(a['report_peak_rss_kib'],1,ADDRESS_SPACE_BYTES//1024)
        arms.append(a)
    predictions={'P1':True,'P2':any(a['rows'][3]['charge_reduction_vs61']>0 for a in arms),
        'P3':next(a for a in arms if a['cohort']=='naming')['naming_largest_positive_exceeds4'],
        'P4':any(a['rows'][256]['charge_reduction_vs61']>0 for a in arms),
        'P5':any(a['rows'][256]['integer_lower_bound']>0 for a in arms)}
    return {'schema':'gamma.required-joint-path-cap.report.v1','complete':True,'validation_loaded':False,
        'contract_sha256':contract,'arms':arms,'predictions':predictions,'population':'fixed300_fit_only',
        **{'parent'+n+'_evidence_sha256':c['public_files'][b.PUBLIC[n]] for n in ('56','57','60','61')},
        'feasibility59_sha256':c['public_files'][b.PUBLIC['59']],
        'production_results_sha256':sha(run/'results.json'),'production_supervisor_sha256':sha(run/'supervisor.json'),
        'production_seconds':production['seconds'],'report_seconds':elapsed,**INHERITANCE,
        'ancestral_private_union':8,'ancestral_files_per_phase':6,'q_or_seed_opened':False,
        'validation_or_cases_opened':False,'new_packets':0,'fresh_qualification_jobs':0,
        'qualification':'Exact original13 receipt reuse; item23 unchanged-source exit137 remains separate.',
        'feasibility_scope':'Item59 existing-seed authority establishes minimum feasible k3; no new witness.',
        'fraction_scope':'Fixed-q required-owner joint bound only; nonpositive is inconclusive.',
        'm1_claim':False,'promotion_allowed':False,'current_best_changed':False}


def failure_result(error):
    return {'schema':'gamma.required-joint-path-cap.report.v1','complete':False,'validation_loaded':False,
        'failure_type':type(error).__name__ if isinstance(error,BaseException) else 'ReportFailure',
        'verdicts':None,'predictions':dict.fromkeys(('P1','P2','P3','P4','P5')),'promotion_allowed':False}


def markdown(result):
    if result['complete'] is not True:return '# Item62 incomplete\n\nNo verdict; incomplete execution or replay.\n'
    lines=['# Item62 required-owner joint caps','',
        'Item60 full-graph science is inherited. Forced owners, all coverage recurrences and constrained allocations are freshly replayed. No q or new packets.']
    for arm in result['arms']:
        lines+=['',arm['cohort'],'','| Bound | k3 bound | Largest positive k | k256 bound |',
                '| --- | ---: | ---: | ---: |']
        for name,row in arm['comparison'].items():
            lines.append(f"| {name} | {row['k3']['integer_lower_bound']} | {row['largest_positive_k']} | {row['k256']['integer_lower_bound']} |")
        lines+=['','Descriptive split counts (j>=3): '+json.dumps(arm['split_counts'],sort_keys=True)]
    naming=next(arm for arm in result['arms'] if arm['cohort']=='naming')
    lines+=['','Naming largest positive budget exceeds4: '+str(naming['naming_largest_positive_exceeds4'])+'.',
        '', 'Budgets0–2 are empty/null. Item59 supplies existing-seed feasibility of at-most classes3..256; numerical allocation does not establish exact-count feasibility.',
        '', 'Predictions: '+json.dumps(result['predictions'],sort_keys=True),
        '', 'All257 curves, raw/integer deltas and numeric split charges are retained. Equal final curves need not mean all joint caps are inactive at individual splits.',
        '', 'No M1, current-best or promotion claim. Exact original13 qualification is reused; item23 exit137 remains separate.']
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
        inputs = binding.load_inputs(config, Path(work), cohort, 'report', effective)
        phase = 'fresh_independent_replay'
        proof_path = Path(output)/(cohort+'-proof.json')
        checked = replay(cohort, inputs, raw, config)
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
