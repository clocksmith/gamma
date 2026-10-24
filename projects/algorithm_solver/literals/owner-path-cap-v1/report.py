"""Independent item57 certificate replay; private inputs require accepted production.

The measured independent checker is immutable. Public output contains selected
hashes, counts and numerical certificate rows, never source or top-entry text
or identities. Shared input/parser and item33 index dependencies are disclosed.
"""
import signal
import time


class HardDeadline(BaseException):
    pass


def _expired(*_):
    raise HardDeadline('independent report deadline')


BOOT_STARTED = time.monotonic() if __name__ == '__main__' else None
if BOOT_STARTED is not None:
    signal.signal(signal.SIGALRM, _expired)
    signal.setitimer(signal.ITIMER_REAL, 600)

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import sys

HERE = Path(__file__).resolve().parent
WORKER_SECONDS = 600
PHASE_SECONDS = 1200
ADDRESS_SPACE_BYTES = 8*1024**3
COHORTS = ('R', 'naming')
def integer(value, minimum=None, maximum=None):
    assert type(value) is int
    assert minimum is None or value >= minimum
    assert maximum is None or value <= maximum
    return value


def number(value, maximum=None):
    assert type(value) in (int, float) and math.isfinite(value) and value >= 0
    assert maximum is None or value <= maximum
    return value


def shaped(value):
    """Normalize tuple/JSON key representation, never bool/integer semantics."""
    if type(value) is dict:
        assert all(type(key) in (str, int) for key in value)
        result = {str(key): shaped(item) for key, item in value.items()}
        assert len(result) == len(value)
        return result
    if type(value) in (list, tuple):
        return [shaped(item) for item in value]
    assert type(value) in (str, int, float, bool, type(None))
    if type(value) is float:
        assert math.isfinite(value)
    return value


def exact(actual, expected):
    assert type(actual) is type(expected), (type(actual).__name__, type(expected).__name__)
    if type(expected) is dict:
        assert actual.keys() == expected.keys()
        for key in expected:
            exact(actual[key], expected[key])
    elif type(expected) is list:
        assert len(actual) == len(expected)
        for left, right in zip(actual, expected):
            exact(left, right)
    else:
        assert actual == expected


def digest(value):
    return hashlib.sha256(json.dumps(shaped(value), sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hash_string(value):
    assert type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)
    return value


def read(path):
    # Reject repeated keys rather than silently accepting an ambiguous receipt.
    def unique(pairs):
        output = {}
        for key, value in pairs:
            assert key not in output, 'duplicate JSON key'
            output[key] = value
        return output
    return json.loads(Path(path).read_text(), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def write(path, value):
    path = Path(path)
    temporary = path.with_name(path.name+'.pending')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def config_limits(config):
    assert config['active'] is True
    expected = {'worker_seconds': WORKER_SECONDS, 'production_seconds': PHASE_SECONDS,
                'report_seconds': PHASE_SECONDS, 'cleanup_seconds': 10,
                'address_space_bytes': ADDRESS_SPACE_BYTES,
                'arm_cores': {'R': [6], 'naming': [7]}}
    for key, value in expected.items():
        exact(config['limits'][key], value)
    assert type(config['fit_ids']) is list and len(config['fit_ids']) == 300
    assert len(set(config['fit_ids'])) == 300
    for pid in config['fit_ids']:
        integer(pid, 0)



prior = module('owner_cap_report_parent53', HERE.parent/'potential-tightening-v1/report.py')
GEOMETRY_FIELDS=prior.GEOMETRY_FIELDS
COMMON=('schema','owner_caps','owner_top_entries','owner_entry_counts','owner_prefixes','capped_prefixes',
        'one_owner_prefix','marginal_choices','shared_prefix','rows','deltas_vs53')
PRODUCTION_WORK=('owner_unique_range_queries','owner_unique_entries_extracted','repeated_new_occurrence_contributions',
    'schedule_endpoints_inspected','schedule_one_owner_occurrences','shared_prefix_positions')
REPORT_WORK=('owner_entries_streamed','owner_top_entries_retained','schedule_old_occurrences',
    'schedule_endpoints_inspected','schedule_occurrences_admitted','banned_occurrences_matched','marginals_sorted',
    'production_forward_positions_checked','production_forward_endpoints_inspected')
SHARED='Item33 Index/structural verifier; original source/parser binding; unchanged item53 production baseline; independent isolated AC/all-depth scalar replay.'
ARM_FIELDS=set(('schema cohort complete validation_loaded contract_sha256 parent53_evidence_sha256 feasibility59_sha256 '
    'bindings_sha256 source_identity_sha256 banned_set_sha256 parent_certificate_sha256 '
    'baseline53_proof_sha256 baseline53_top_entries_sha256 baseline53_paired_digests '
    'independent_receipt_sha256 production_proof_sha256 scientific_proof_sha256 '
    'owner_caps_sha256 owner_top_entries_sha256 owner_entry_counts_sha256 owner_prefixes_sha256 capped_prefixes_sha256 '
    'production_prefix_schedule_sha256 independent_suffix_schedule_sha256 one_owner_prefix_sha256 marginal_choices_sha256 '
    'shared_prefix_sha256 fit_problems old_pool_entries seed_entries old_occurrences geometry denominator path_numerator '
    'class_counts owner_aggregates rows baseline53_rows deltas_vs53 largest_positive_k baseline53_largest_positive_k '
    'positive_budgets_below_feasible_floor positive_budgets_in_nonempty_classes minimum_feasible_one_owner_budget '
    'production_work report_work baseline_production_work baseline_report_work '
    'production_seconds production_peak_rss_kib production_phase_seconds_sha256 report_worker_seconds report_peak_rss_kib '
    'production_arm_sha256 production_results_sha256 production_supervisor_sha256 '
    'all257_independently_replayed baseline53_reconstructed all_forward_schedule_recurrences_checked shared_dependencies').split())

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
        assert not target.exists(), 'fresh report worker output required'
        fresh = True
        binding = module('owner_path_cap_report_binding', HERE/'binding.py')
        config = read(HERE/'contract.json'); config_limits(config)
        binding.check_contract(config)
        contract_hash = sha(HERE/'contract.json')
        phase = 'production_receipts'
        production, supervisor = accepted_production(run, config, contract_hash)
        raw = next(arm for arm in production['arms'] if arm['cohort'] == cohort)
        phase = 'input_identity'
        inputs = binding.load_inputs(config, Path(work), cohort, effective)
        phase = 'fresh_independent_replay'
        checker = module('owner_path_cap_report_checker', HERE/'independent.py')
        result = replay(cohort, inputs, raw, checker, config['old_arms'][cohort], config['parent50_arms'][cohort], config['parent53_arms'][cohort], Path(output)/(cohort+'-proof.json'))
        result.update(parent53_evidence_sha256=config['parent53_evidence']['sha256'],
                      feasibility59_sha256=config['feasibility59']['sha256'],
                      independent_receipt_sha256=sha(Path(output)/(cohort+'-proof.json')),
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




def parents(config):
    for key in ('parent50_contract','parent50_evidence','parent53_contract','parent53_evidence','feasibility59'):
        pin=config[key];assert set(pin)=={'path','sha256'}
        assert sha(HERE.parent/pin['path'])==pin['sha256']
    r=read(HERE.parent/config['parent53_evidence']['path'])
    assert r['schema']=='gamma.potential-tightening.report.v1' and r['complete'] is True
    assert r['validation_loaded'] is r['validation_or_cases_opened'] is False
    assert r['contract_sha256']==config['parent53_contract']['sha256'] and r['predictions']['P1'] is True
    exact({a['cohort']:a for a in r['arms']},config['parent53_arms'])
    feasibility=read(HERE.parent/config['feasibility59']['path'])
    assert feasibility['complete'] is True and feasibility['capacity']==256
    assert feasibility['fit_id_set_sha256']==digest(sorted(config['fit_ids']))
    for p,h in feasibility['public_files'].items():assert sha(HERE.parent/p)==h
    assert [a['cohort'] for a in feasibility['arms']]==list(COHORTS)
    for a in feasibility['arms']:
        assert a['minimum_feasible_one_owner_budget']==3 and a['nonempty_at_most_budget_range']==[3,256]
        assert a['source_identity_sha256']==config['parent53_arms'][a['cohort']]['source_identity_sha256']
    return config['parent53_arms']


def scientific(proof):
    return {key:proof[key] for key in COMMON}|{'base':{key:proof['base'][key] for key in prior.SCIENTIFIC_FIELDS}}


def owner_shape(proof,geometry):
    assert set(proof)==set(COMMON)|{'base','owner_prefix_schedule','digests','work'}
    assert proof['schema']=='gamma.owner-path-cap.supplied.v1'
    base=proof['base'];prior.paired_shape(base);p=base['tightened'];ids=set(p['path_numerators'])
    assert all(set(proof[key])==ids for key in ('owner_caps','owner_top_entries','owner_entry_counts',
               'owner_prefixes','capped_prefixes','owner_prefix_schedule'))
    total_entries=0;global_top=[];marginals=[];positions=0;endpoints=0
    for pid in sorted(ids):
        cap=integer(proof['owner_caps'][pid],0);count=integer(proof['owner_entry_counts'][pid],0)
        total_entries+=count;entries=proof['owner_top_entries'][pid]
        assert type(entries) is list and len(entries)==min(256,count)
        assert all(type(e) is list and len(e)==3 for e in entries)
        for w,g,n in entries:integer(w,0);integer(g,0,geometry['full_groups']-1);integer(n,1)
        assert entries==sorted(entries,key=lambda x:(-x[0],x[1],x[2]))
        assert len({(e[1],e[2]) for e in entries})==len(entries)
        global_top+=entries;prefix=[0]
        for weight,_,_ in entries:prefix.append(prefix[-1]+weight)
        exact(proof['owner_prefixes'][pid],prefix)
        clipped=[min(v,cap) for v in prefix];exact(proof['capped_prefixes'][pid],clipped)
        differences=[b-a for a,b in zip(clipped,clipped[1:])]
        assert differences==sorted(differences,reverse=True)
        marginals.extend((v,pid,j) for j,v in enumerate(differences,1))
        vector=proof['owner_prefix_schedule'][pid]
        assert type(vector) is list and len(vector)>1
        for v in vector:integer(v,0)
        assert vector[0]==0 and vector[-1]==cap and vector==sorted(vector)
        n=len(vector)-1;positions+=n;endpoints+=n*(n+1)//2
    assert total_entries==p['class_counts']['1'] and positions==geometry['source_characters']
    assert len({(e[1],e[2]) for e in global_top})==len(global_top)
    exact(sorted(global_top,key=lambda x:(-x[0],x[1],x[2]))[:256],p['top_entries']['1'])
    chosen=sorted(marginals,key=lambda v:(-v[0],v[1],v[2]))[:256]
    exact(proof['marginal_choices'],[[pid,j,v] for v,pid,j in chosen])
    one=[0]
    for v,_,_ in chosen:one.append(one[-1]+v)
    exact(proof['one_owner_prefix'],one);shared=[0]
    for weight,_,_ in p['top_entries']['2']:shared.append(shared[-1]+weight)
    exact(proof['shared_prefix'],shared);D=p['denominator'];L=sum(p['path_numerators'].values())
    assert len(proof['rows'])==len(proof['deltas_vs53'])==257
    for k,(row,delta,old) in enumerate(zip(proof['rows'],proof['deltas_vs53'],p['rows'])):
        charge,negj=max((one[j]+shared[min(256-j,len(shared)-1)],-j) for j in range(min(k,len(one)-1)+1))
        expected={'k':k,'charge':charge,'one_owner_slots':-negj,'shared_slots':min(256+negj,len(shared)-1),
                  'numerator':L-charge,'integer_lower_bound':-(-(L-charge)//D)}
        exact(row,expected);assert charge<=old['charge']
        exact(delta,{'k':k,'charge_reduction':old['charge']-charge,
                     'integer_bound_gain':row['integer_lower_bound']-old['integer_lower_bound']})
    keys=set(COMMON)-{'schema'}|{'owner_prefix_schedule'}
    assert set(proof['digests'])=={key+'_sha256' for key in keys}|{'base_paired_sha256'}
    for key in keys:assert proof['digests'][key+'_sha256']==digest(proof[key])
    assert proof['digests']['base_paired_sha256']==digest({key:base[key] for key in prior.SCIENTIFIC_FIELDS if key!='schema'})
    w=proof['work'];assert set(w)==set(PRODUCTION_WORK)
    for value in w.values():integer(value,0)
    assert w['schedule_endpoints_inspected']==endpoints and w['shared_prefix_positions']==positions
    assert w['schedule_one_owner_occurrences']<=endpoints
    assert w['owner_unique_entries_extracted']<=256*len(ids)
    assert w['owner_unique_range_queries']>=w['owner_unique_entries_extracted']


def independent_shape(raw,checked,geometry):
    owner_shape(raw,geometry)
    for key in COMMON:exact(raw[key],checked[key])
    for key in prior.SCIENTIFIC_FIELDS:exact(raw['base'][key],checked['base'][key])
    base=checked['base'];exact(base['geometry'],geometry)
    prior.check_work(raw['base'],base['work'],geometry)
    assert base['shared_dependency']=='item33 Index and verify partition/suffix/ban checks'
    assert base['scalar_replay']=='AC/end-order paths; owner-run ends; all-depth exact sums'
    assert set(base)==set(prior.SCIENTIFIC_FIELDS)|{'geometry','work','shared_dependency','scalar_replay'}
    assert set(checked)==set(COMMON)|{'base','owner_suffix_schedule','digests','work','shared_dependency','scalar_replay',
        'production_forward_schedule_checked','production_forward_schedule_sha256'}
    assert checked['production_forward_schedule_checked'] is True
    assert checked['production_forward_schedule_sha256']==digest(raw['owner_prefix_schedule'])
    assert set(checked['owner_suffix_schedule'])==set(raw['owner_caps'])
    for pid,values in checked['owner_suffix_schedule'].items():
        assert type(values) is list and len(values)==len(raw['owner_prefix_schedule'][pid])
        for v in values:integer(v,0)
        assert values[0]==raw['owner_caps'][pid] and values[-1]==0 and values==sorted(values,reverse=True)
    keys=set(COMMON)-{'schema'}|{'owner_suffix_schedule'}
    assert set(checked['digests'])=={key+'_sha256' for key in keys}|{'base_paired_sha256'}
    for key in keys:assert checked['digests'][key+'_sha256']==digest(checked[key])
    assert checked['digests']['base_paired_sha256']==raw['digests']['base_paired_sha256']
    assert checked['shared_dependency']=='item33 Index and verify partition/suffix/ban checks'
    assert checked['scalar_replay']=='isolated item53 AC replay; bounded sorted owner tops; fresh AC shared/ban matching; backward schedule; sorted marginals'
    w=checked['work'];assert set(w)==set(REPORT_WORK)
    for value in w.values():integer(value,0)
    assert w['owner_entries_streamed']==sum(raw['owner_entry_counts'].values())
    assert w['owner_top_entries_retained']==sum(map(len,raw['owner_top_entries'].values()))
    assert w['marginals_sorted']==w['owner_top_entries_retained']
    assert w['schedule_old_occurrences']==raw['base']['tightened']['old_occurrences']
    assert w['production_forward_positions_checked']==geometry['source_characters']
    assert w['production_forward_endpoints_inspected']==w['schedule_endpoints_inspected']==raw['work']['schedule_endpoints_inspected']
    assert w['schedule_occurrences_admitted']==raw['work']['schedule_one_owner_occurrences']
    assert w['banned_occurrences_matched']==geometry['exact_ban_occurrences']

def accepted_production(run, config, contract_hash):
    """Only run receipts are read here; this must precede all nine-file access."""
    config_limits(config)
    parents(config)
    run = Path(run)
    assert not (run/'failure.json').exists()
    for cohort in COHORTS:
        assert not (run/(cohort+'-failure.json')).exists()
        assert not (run/cohort/'failure.json').exists()
    production, supervisor = read(run/'results.json'), read(run/'supervisor.json')
    assert production['complete'] is supervisor['complete'] is True
    assert production['validation_loaded'] is False and supervisor['phase'] == 'production'
    assert production['contract_sha256'] == supervisor['contract_sha256'] == contract_hash
    codes = supervisor['returncodes']
    assert type(codes) is list and len(codes) == 2
    assert all(type(code) is int and code == 0 for code in codes)
    number(supervisor['cleanup_seconds'], 10)
    number(supervisor['elapsed'], PHASE_SECONDS)
    number(production['seconds'], PHASE_SECONDS)
    assert production['seconds'] <= supervisor['elapsed']
    assert type(production['arms']) is list and len(production['arms']) == 2
    assert [arm['cohort'] for arm in production['arms']] == list(COHORTS)
    for arm in production['arms']:
        assert arm['complete'] is True and arm['validation_loaded'] is False
        assert arm['contract_sha256'] == contract_hash
        number(arm['seconds'], WORKER_SECONDS)
        assert arm['seconds'] <= production['seconds']
        integer(arm['peak_rss_kib'], 1, ADDRESS_SPACE_BYTES//1024)
        assert type(arm['phase_seconds']) is dict
        assert set(arm['phase_seconds'])=={'input','proof'}
        assert all(type(key) is str for key in arm['phase_seconds'])
        for value in arm['phase_seconds'].values():
            number(value, arm['seconds'])
        assert sum(arm['phase_seconds'].values()) <= arm['seconds']
        assert type(arm['bindings']) is dict
        assert set(arm['full_shape']) == set(GEOMETRY_FIELDS)
        for value in arm['full_shape'].values():
            integer(value, 0)
        assert arm['schema'] == 'gamma.owner-path-cap.arm.v1'
        owner_shape(arm['proof'],arm['full_shape'])
        assert set(arm['proof']['base']['lifted']['path_numerators']) == {str(pid) for pid in config['fit_ids']}
        exact(read(run/arm['cohort']/'results.json'), arm)
    return production, supervisor




def compare53(raw,inputs,checked,geometry,expected):
    # Public reconstruction shared with production; no path/top computation is
    # delegated. The checker has already independently rebuilt every term.
    base=checked['base'];p=base['tightened'];paths=p['path_numerators'];D=p['denominator']
    values={'bindings_sha256':digest(inputs['bindings']),'source_identity_sha256':digest(inputs['source_hashes']),
        'banned_set_sha256':digest(sorted(inputs['banned'])),'parent_certificate_sha256':digest(inputs['parent_certificate']),
        'checked_proof_sha256':digest({key:base[key] for key in prior.SCIENTIFIC_FIELDS}),
        'top_entries_sha256':digest(p['top_entries']),'old_occurrence_order_sha256':p['occurrence_sha256'],
        'old_path_terms_sha256':digest([paths[pid] for pid in sorted(paths)]),
        'fit_problems':len(inputs['texts']),'old_pool_entries':len(inputs['pool']),'seed_entries':len(inputs['seed']),
        'old_occurrences':p['old_occurrences'],'geometry':geometry,'denominator':D,'path_numerator':sum(paths.values()),
        'old_charge':p['old_charge'],'old_numerator':p['old_numerator'],'old_integer_lower_bound':-(-p['old_numerator']//D),
        'class_counts':p['class_counts'],'rows':p['rows'],'lifted_rows':base['lifted']['rows'],'paired_digests':base['digests'],
        'reductions':base['reductions'],'deltas':base['deltas'],'new_only_class_counts':base['new_only_class_counts'],
        'largest_positive_k':prior.positive_k(p),'lifted_largest_positive_k':prior.positive_k(base['lifted'])}
    for key,value in values.items():exact(expected[key],value)


def baseline_metadata(raw,expected):
    base=raw['proof']['base'];p=base['tightened'];paths=p['path_numerators']
    for key,value in {'bindings_sha256':digest(raw['bindings']),
        'source_identity_sha256':raw['bindings']['source_hashes_sha256'],'banned_set_sha256':raw['bindings']['bans_sha256'],
        'checked_proof_sha256':digest({key:base[key] for key in prior.SCIENTIFIC_FIELDS}),
        'top_entries_sha256':digest(p['top_entries']),'rows':p['rows'],'lifted_rows':base['lifted']['rows'],
        'paired_digests':base['digests'],'reductions':base['reductions'],'deltas':base['deltas'],
        'new_only_class_counts':base['new_only_class_counts'],'geometry':raw['full_shape'],
        'class_counts':p['class_counts'],'path_numerator':sum(paths.values()),'denominator':p['denominator'],
        'old_charge':p['old_charge'],'old_numerator':p['old_numerator'],
        'old_integer_lower_bound':-(-p['old_numerator']//p['denominator']),
        'old_occurrences':p['old_occurrences'],'old_occurrence_order_sha256':p['occurrence_sha256'],
        'old_path_terms_sha256':digest([paths[pid] for pid in sorted(paths)]),
        'largest_positive_k':prior.positive_k(p),'lifted_largest_positive_k':prior.positive_k(base['lifted'])}.items():exact(expected[key],value)


def replay(cohort,inputs,raw,checker,expected_old,expected50,expected53,receipt):
    texts,banned=inputs['texts'],inputs['banned'];exact(raw['bindings'],shaped(inputs['bindings']))
    index=checker.full.Index(texts,banned)
    checker.full.verify(index,{pid:[0]*len(text) for pid,text in texts.items()},0,1)
    geometry={'source_characters':len(index.positions),'full_groups':len(index.groups),
        'full_distinct_entries':index.distinct_allowed_entries,
        'exact_ban_occurrences':sum(len(ends) for rows in index.banned_ends.values() for ends in rows)}
    exact(raw['full_shape'],geometry);exact(shaped(inputs['geometry']),geometry);del index
    assert {w for w in inputs['pool'] if len(w)==1}==set(inputs['alphabet'])
    extras=sorted(w for w in inputs['seed'] if len(w)>1 and sum(w in t for t in texts.values())<2)
    for key,value in {'pool_entries':len(inputs['pool']),'maximum_entry_length':max(map(len,inputs['pool'])),
        'occurrences':len(inputs['q']),'seed_extra_entries':len(extras),
        'shared_learned_entries':sum(len(w)>1 for w in inputs['pool'])-len(extras),
        'seed_extras_sha256':hashlib.sha256(json.dumps(extras,ensure_ascii=True).encode()).hexdigest()}.items():exact(expected_old[key],value)
    checked=shaped(checker.check(texts,banned,inputs['pool'],inputs['q'],inputs['seed'],inputs['alphabet'],inputs['denominator'],
        expected_source_hashes=inputs['source_hashes'],expected_old_banned=banned,
        expected_old_certificate=inputs['parent_certificate'],expected_occurrence_sha256=expected50['old_occurrence_order_sha256'],
        expected_prefix_schedule=raw['proof']['owner_prefix_schedule']))
    independent_shape(raw['proof'],checked,geometry)
    compare53(raw,inputs,checked,geometry,expected53)
    fake={**raw,'proof':raw['proof']['base']}
    basepublic=prior.sanitize(cohort,inputs,fake,checked['base'],geometry)
    prior.compare50(cohort,basepublic,checked['base']['lifted'],expected50)
    write(receipt,checked)
    return public_arm(cohort,raw,checked,expected53)


def public_arm(cohort,raw,checked,expected):
    proof=raw['proof'];base=proof['base'];p=base['tightened'];caps=proof['owner_caps']
    baseline_metadata(raw,expected)
    aggregates={'owners':len(caps),'positive_caps':sum(v>0 for v in caps.values()),'cap_sum':sum(caps.values()),
        'cap_max':max(caps.values(),default=0),'top_entries_retained':sum(map(len,proof['owner_top_entries'].values())),
        'full_one_owner_entries':sum(proof['owner_entry_counts'].values()),
        'owners_with_clipped_prefix':sum(proof['owner_prefixes'][pid][-1]>caps[pid] for pid in caps)}
    result={'schema':'gamma.owner-path-cap.report-arm.v1','cohort':cohort,'complete':True,'validation_loaded':False,
        'contract_sha256':raw['contract_sha256'],'bindings_sha256':digest(raw['bindings']),
        'source_identity_sha256':expected['source_identity_sha256'],'banned_set_sha256':expected['banned_set_sha256'],
        'parent_certificate_sha256':expected['parent_certificate_sha256'],
        'baseline53_proof_sha256':expected['checked_proof_sha256'],'baseline53_top_entries_sha256':expected['top_entries_sha256'],
        'baseline53_paired_digests':base['digests'],'production_proof_sha256':digest(proof),
        'scientific_proof_sha256':digest(scientific(checked)),
        'production_prefix_schedule_sha256':digest(proof['owner_prefix_schedule']),
        'independent_suffix_schedule_sha256':digest(checked['owner_suffix_schedule']),
        'fit_problems':len(caps),'old_pool_entries':expected['old_pool_entries'],'seed_entries':expected['seed_entries'],
        'old_occurrences':p['old_occurrences'],'geometry':raw['full_shape'],'denominator':p['denominator'],
        'path_numerator':sum(p['path_numerators'].values()),'class_counts':p['class_counts'],'owner_aggregates':aggregates,
        'rows':proof['rows'],'baseline53_rows':p['rows'],'deltas_vs53':proof['deltas_vs53'],
        'largest_positive_k':prior.positive_k(proof),'baseline53_largest_positive_k':prior.positive_k(p),
        'positive_budgets_below_feasible_floor':[r['k'] for r in proof['rows'] if r['k']<3 and r['integer_lower_bound']>0],
        'positive_budgets_in_nonempty_classes':[r['k'] for r in proof['rows'] if r['k']>=3 and r['integer_lower_bound']>0],
        'minimum_feasible_one_owner_budget':3,'production_work':proof['work'],'report_work':checked['work'],
        'baseline_production_work':base['work'],'baseline_report_work':checked['base']['work'],
        'production_seconds':raw['seconds'],'production_peak_rss_kib':raw['peak_rss_kib'],
        'production_phase_seconds_sha256':digest(raw['phase_seconds']),'all257_independently_replayed':True,
        'baseline53_reconstructed':True,'all_forward_schedule_recurrences_checked':True,'shared_dependencies':SHARED}
    for key in ('owner_caps','owner_top_entries','owner_entry_counts','owner_prefixes','capped_prefixes',
                'one_owner_prefix','marginal_choices','shared_prefix'):result[key+'_sha256']=digest(proof[key])
    return result


def combine(run,output,config,elapsed,returncodes):
    run,output=Path(run),Path(output);assert not (output/'failure.json').exists()
    config_limits(config);number(elapsed,PHASE_SECONDS)
    assert type(returncodes) is list and len(returncodes)==2 and all(type(v) is int and v==0 for v in returncodes)
    ch=sha(HERE/'contract.json');production,supervisor=accepted_production(run,config,ch);expected=parents(config);arms=[]
    for cohort,raw in zip(COHORTS,production['arms']):
        assert not (output/(cohort+'-failure.json')).exists()
        arm=read(output/(cohort+'.json'));assert set(arm)==ARM_FIELDS
        checked=read(output/(cohort+'-proof.json'))
        assert arm['independent_receipt_sha256']==sha(output/(cohort+'-proof.json'))
        independent_shape(raw['proof'],checked,raw['full_shape'])
        rebuilt=public_arm(cohort,raw,checked,expected[cohort])
        for key,value in rebuilt.items():exact(arm[key],value)
        assert arm['source_identity_sha256']==digest(config['source_hashes'][cohort])
        assert arm['parent_certificate_sha256']==digest(config['old_arms'][cohort]['certificate'])
        for key,p in (('production_arm_sha256',run/cohort/'results.json'),('production_results_sha256',run/'results.json'),
                      ('production_supervisor_sha256',run/'supervisor.json')):assert arm[key]==sha(p)
        assert arm['parent53_evidence_sha256']==config['parent53_evidence']['sha256']
        assert arm['feasibility59_sha256']==config['feasibility59']['sha256']
        number(arm['report_worker_seconds'],min(WORKER_SECONDS,elapsed));integer(arm['report_peak_rss_kib'],1,ADDRESS_SPACE_BYTES//1024)
        for key in ARM_FIELDS:
            if key.endswith('_sha256'):hash_string(arm[key])
        arms.append(arm)
    preds={'P1':True,'P2':any(d['charge_reduction']>0 for a in arms for d in a['deltas_vs53']),
        'P3':any((a['largest_positive_k'] if a['largest_positive_k'] is not None else -1)>
                 (a['baseline53_largest_positive_k'] if a['baseline53_largest_positive_k'] is not None else -1) for a in arms),
        'P4':any(a['positive_budgets_in_nonempty_classes'] for a in arms),
        'P5':any(a['rows'][256]['integer_lower_bound']>0 for a in arms)}
    return {'schema':'gamma.owner-path-cap.report.v1','complete':True,'validation_loaded':False,'population':'fixed300_fit_only',
        'contract_sha256':ch,'parent53_evidence_sha256':config['parent53_evidence']['sha256'],
        'feasibility59_sha256':config['feasibility59']['sha256'],'production_results_sha256':sha(run/'results.json'),
        'production_supervisor_sha256':sha(run/'supervisor.json'),'production_seconds':production['seconds'],
        'report_seconds':elapsed,'arms':arms,'predictions':preds,
        'verdicts':{'baseline53_exactly_reconstructed':True,'pointwise_dominance':True,'all257_per_cohort_replayed':True,
                    'all_production_forward_recurrences_checked':True},
        'qualification':{'authority':'Exact original item13 source-hash qualification only','fresh_jobs':0,'new_witness_packets':0,
                         'inherited_failure':'Item23 later unchanged-source exit137 remains separate.'},
        'coverage_scope':'Item59 establishes minimum support3 at capacity256; k<3 empty, every at-most-k>=3 nonempty by existing seed.',
        'fraction_scope':'Positive bound excludes C/N<=10% in that fixed support class; nonpositive bound inconclusive; no optimization over q or d.',
        'shared_dependencies':SHARED,'m1_claim':False,'packet_or_witness_claim':False,'new_qualification_claim':False,
        'validation_or_cases_opened':False,'optimality_claim':False,'promotion_allowed':False}


def failure_result(error):
    return {'schema':'gamma.owner-path-cap.report.v1','complete':False,'validation_loaded':False,
        'failure_type':type(error).__name__ if isinstance(error,BaseException) else 'ReportFailure','verdicts':None,
        'predictions':{key:None for key in ('P1','P2','P3','P4','P5')},'m1_claim':False,'packet_or_witness_claim':False,'promotion_allowed':False}


def markdown(result):
    if result['complete'] is not True:return '# Item 57 incomplete\n\nNo verdict; incomplete execution or independent replay.\n'
    lines=['# Item 57 fixed-penalty owner path caps','',
        '| Cohort | Item53 bound at k=3 | New bound at k=3 | Baseline k* | New k* | Positive budgets in nonempty classes k>=3 | Sum owner caps | Clipped owner prefixes |',
        '| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |']
    for a in result['arms']:
        lines.append(f"| {a['cohort']} | {a['baseline53_rows'][3]['integer_lower_bound']} | {a['rows'][3]['integer_lower_bound']} | {a['baseline53_largest_positive_k']} | {a['largest_positive_k']} | {a['positive_budgets_in_nonempty_classes']} | {a['owner_aggregates']['cap_sum']} | {a['owner_aggregates']['owners_with_clipped_prefix']} |")
    lines+=['','Predictions: '+json.dumps(result['predictions'],sort_keys=True),'',result['coverage_scope'],result['fraction_scope'],'',
        'All 257 rows, raw charge reductions and integer-bound gains are retained. Every production forward scheduling recurrence is checked independently, alongside fresh backward schedules and exact owner tops. The charge bounds used path penalties; it is not an upper bound on a dictionary’s full occurrence-weight sum.',
        '',SHARED,'','No private53 inputs, validation, new source execution, multiplier optimization, fresh qualification or witness packets. Original13 qualification reuse only; item23 unchanged-source exit137 remains separate. No M1 or promotion claim.']
    return '\n'.join(lines)+'\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cohort', choices=COHORTS, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--deadline', type=float, required=True)
    args = parser.parse_args()
    worker(args.cohort, args.work, args.run, args.output, args.deadline)
