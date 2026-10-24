"""Independent item56 certificate replay; private inputs require accepted production.

Public output contains selected hashes and counts, never sources, pool entries
or per-source identities. Accepted item50 completeness, the input parser and
the item50 AC matcher are explicit shared dependencies.
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
COMMON_FIELDS = {'shared_entry_ids','owner_classes','source_success','forced_source_ids',
    'private_character_source_ids','private_character_entries','occurrences','occurrence_sha256'}
SHARED = 'Accepted item50 shared-pool completeness; original parser and input hashes; unchanged item50 AC matcher.'
ARM_FIELDS = set(('schema complete validation_loaded cohort contract_sha256 parent50_evidence_sha256 '
    'bindings_sha256 source_identity_sha256 banned_set_sha256 source_file_sha256 pool_file_sha256 '
    'fit_problems source_characters pool_entries shared_entries one_owner_pool_entries absent_pool_entries '
    'occurrences occurrence_sha256 coverage_floor private_character_floor private_character_entries coverable_sources '
    'source_success_sha256 owner_classes_sha256 shared_entry_ids_sha256 forced_source_ids_sha256 '
    'private_character_source_ids_sha256 production_prefix_sha256 independent_suffix_sha256 independent_proof_sha256 '
    'largest_positive_k positive50_budgets positive_budgets_below_floor positive_budgets_not_ruled_out '
    'positive_bound_remaining production_seconds production_phase_seconds_sha256 production_peak_rss_kib '
    'report_worker_seconds report_peak_rss_kib production_arm_sha256 production_results_sha256 '
    'production_supervisor_sha256 shared_dependencies all_sources_independently_replayed '
    'all_prefix_suffix_recurrences_checked').split())


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


def parent50(config):
    for pin in (config['parent50_contract'],config['parent50_evidence']):
        assert set(pin)=={'path','sha256'}
        assert sha(HERE.parent/pin['path'])==hash_string(pin['sha256'])
    value=read(HERE.parent/config['parent50_evidence']['path'])
    assert value['schema']=='gamma.potential-lift.report.v1' and value['complete'] is True
    assert value['contract_sha256']==config['parent50_contract']['sha256']
    assert value['validation_loaded'] is False and value['validation_or_cases_opened'] is False
    assert value['verdicts']['all257_replayed'] is True and value['verdicts']['k0_preserves_old_bound'] is True
    assert [a['cohort'] for a in value['arms']]==list(COHORTS)
    exact({a['cohort']:a for a in value['arms']},config['parent50_arms'])
    for a in value['arms']:
        assert a['complete'] is True and a['validation_loaded'] is False
        for flag in ('all257_independently_replayed','old_certificate_independently_replayed','suffix_potential_proof_checked'):assert a[flag] is True
        assert a['contract_sha256']==config['parent50_contract']['sha256']
        assert len(a['rows'])==257
        for k,row in enumerate(a['rows']):
            assert row['k']==k and all(type(v) is int for v in row.values())
            assert row['numerator']==a['path_numerator']-row['charge']
            assert row['integer_lower_bound']==-(-row['numerator']//a['denominator'])
    return config['parent50_arms']


def proof_shape(proof,expected,ids,direction='prefix_reachable'):
    assert set(proof)==COMMON_FIELDS|{direction}
    assert type(proof['owner_classes']) is list and len(proof['owner_classes'])==expected['old_pool_entries']
    assert all(type(v) is int and v in (0,1,2) for v in proof['owner_classes'])
    exact(proof['shared_entry_ids'],[i for i,v in enumerate(proof['owner_classes']) if v==2])
    assert len(proof['shared_entry_ids'])==expected['class_counts']['2']
    assert set(proof['source_success'])==set(ids) and all(type(v) is bool for v in proof['source_success'].values())
    exact(proof['forced_source_ids'],sorted(pid for pid,ok in proof['source_success'].items() if not ok))
    private=proof['private_character_source_ids']
    assert type(private) is list and all(type(pid) is str for pid in private)
    assert private==sorted(set(private)) and set(private)<=set(proof['forced_source_ids'])
    exact(private,proof['forced_source_ids'])
    integer(proof['private_character_entries'],len(private),96)
    exact(proof['occurrences'],expected['old_occurrences'])
    assert hash_string(proof['occurrence_sha256'])==expected['old_occurrence_order_sha256']
    assert set(proof[direction])==set(ids)
    for pid,vector in proof[direction].items():
        assert type(vector) is list and len(vector)>1 and all(type(v) is bool for v in vector)
        if direction=='prefix_reachable':assert vector[0] is True and vector[-1] is proof['source_success'][pid]
        else:assert vector[-1] is True and vector[0] is proof['source_success'][pid]
    assert sum(len(v)-1 for v in proof[direction].values())==expected['geometry']['source_characters']


def accepted_production(run,config,contract_hash):
    config_limits(config);parents=parent50(config);run=Path(run)
    assert not (run/'failure.json').exists()
    production,supervisor=read(run/'results.json'),read(run/'supervisor.json')
    assert production['complete'] is supervisor['complete'] is True
    assert production['validation_loaded'] is False and supervisor['phase']=='production'
    assert production['contract_sha256']==supervisor['contract_sha256']==contract_hash
    assert type(supervisor['returncodes']) is list and len(supervisor['returncodes'])==2
    assert all(type(v) is int and v==0 for v in supervisor['returncodes'])
    number(supervisor['cleanup_seconds'],10);number(supervisor['elapsed'],PHASE_SECONDS)
    number(production['seconds'],supervisor['elapsed'])
    assert [a['cohort'] for a in production['arms']]==list(COHORTS)
    for raw in production['arms']:
        cohort=raw['cohort']
        assert not (run/cohort/'failure.json').exists() and not (run/(cohort+'-failure.json')).exists()
        assert raw['schema']=='gamma.support-coverage-floor.arm.v1'
        assert raw['complete'] is True and raw['validation_loaded'] is False and raw['contract_sha256']==contract_hash
        number(raw['seconds'],min(WORKER_SECONDS,production['seconds']));integer(raw['peak_rss_kib'],1,ADDRESS_SPACE_BYTES//1024)
        assert set(raw['phase_seconds'])=={'input','proof'}
        for v in raw['phase_seconds'].values():number(v,raw['seconds'])
        assert sum(raw['phase_seconds'].values())<=raw['seconds']
        proof_shape(raw['proof'],parents[cohort],{str(pid) for pid in config['fit_ids']})
        exact(read(run/cohort/'results.json'),raw)
    return production,supervisor


def check_vectors(texts,pool,production,independent):
    """Fresh AC occurrences check every prefix and suffix boolean recurrence.

    Only the accepted item50 Matcher is shared; these checks neither reuse the
    production trie nor infer intermediate vectors from final source flags.
    """
    matcher=module('support56_report_matcher50',HERE.parent/'potential-lift-certificate-v1/independent.py').Matcher(pool)
    shared=set(independent['shared_entry_ids'])
    for pid,text in texts.items():
        incoming=[[] for _ in range(len(text)+1)];outgoing=[[] for _ in text]
        for start,end,eid in matcher.occurrences(text):
            if eid in shared:incoming[end].append(start);outgoing[start].append(end)
        prefix=production['prefix_reachable'][pid];suffix=independent['suffix_reachable'][pid]
        assert len(prefix)==len(suffix)==len(text)+1 and prefix[0] is suffix[-1] is True
        for end in range(1,len(text)+1):assert prefix[end] is any(prefix[start] for start in incoming[end])
        for start in range(len(text)):assert suffix[start] is any(suffix[end] for end in outgoing[start])


def replay(cohort,inputs,raw,checker,expected,receipt=None):
    texts,pool,banned=inputs['texts'],inputs['pool'],inputs['banned']
    alphabet=set(chr(i) for i in range(32,127))|{'\n'}
    assert alphabet<=set(pool) and not set(pool)&set(banned)
    assert all(set(text)<=alphabet for text in texts.values())
    exact(raw['bindings'],shaped(inputs['bindings']))
    assert digest(inputs['source_hashes'])==expected['source_identity_sha256']
    assert digest(sorted(banned))==expected['banned_set_sha256']
    proof_shape(raw['proof'],expected,set(texts))
    checked=checker.replay(texts,pool,banned)
    proof_shape(checked,expected,set(texts),'suffix_reachable')
    for key in COMMON_FIELDS:exact(raw['proof'][key],checked[key])
    check_vectors(texts,pool,raw['proof'],checked)
    if receipt is not None: write(receipt,checked)
    return sanitize(cohort,inputs,raw,checked,expected)


def summary(proof,expected):
    floor=len(proof['forced_source_ids']);private=len(proof['private_character_source_ids'])
    exact(proof['forced_source_ids'],proof['private_character_source_ids'])
    positive=[row['k'] for row in expected['rows'] if row['integer_lower_bound']>0]
    remaining=[k for k in positive if k>=floor]
    return {'fit_problems':len(proof['source_success']),'source_characters':expected['geometry']['source_characters'],
        'pool_entries':len(proof['owner_classes']),'shared_entries':len(proof['shared_entry_ids']),
        'one_owner_pool_entries':proof['owner_classes'].count(1),'absent_pool_entries':proof['owner_classes'].count(0),
        'occurrences':proof['occurrences'],'occurrence_sha256':proof['occurrence_sha256'],
        'coverage_floor':floor,'private_character_floor':private,'private_character_entries':proof['private_character_entries'],
        'coverable_sources':len(proof['source_success'])-floor,
        'source_success_sha256':digest(proof['source_success']),'owner_classes_sha256':digest(proof['owner_classes']),
        'shared_entry_ids_sha256':digest(proof['shared_entry_ids']),'forced_source_ids_sha256':digest(proof['forced_source_ids']),
        'private_character_source_ids_sha256':digest(proof['private_character_source_ids']),
        'largest_positive_k':max(positive,default=None),'positive50_budgets':positive,
        'positive_budgets_below_floor':[k for k in positive if k<floor],
        'positive_budgets_not_ruled_out':remaining,'positive_bound_remaining':bool(remaining)}


def sanitize(cohort,inputs,raw,checked,expected):
    return {'schema':'gamma.support-coverage-floor.report-arm.v1','complete':True,'validation_loaded':False,
        'cohort':cohort,'contract_sha256':raw['contract_sha256'],'bindings_sha256':digest(inputs['bindings']),
        'source_identity_sha256':digest(inputs['source_hashes']),'banned_set_sha256':digest(sorted(inputs['banned'])),
        'source_file_sha256':inputs['bindings']['source_sha256'],'pool_file_sha256':inputs['bindings']['pool_sha256'],
        **summary(checked,expected),'production_prefix_sha256':digest(raw['proof']['prefix_reachable']),
        'independent_suffix_sha256':digest(checked['suffix_reachable']),
        'production_seconds':raw['seconds'],'production_phase_seconds_sha256':digest(raw['phase_seconds']),
        'production_peak_rss_kib':raw['peak_rss_kib'],'shared_dependencies':SHARED,
        'all_sources_independently_replayed':True,'all_prefix_suffix_recurrences_checked':True}


def failure_result(error):
    # Exception strings can contain source paths or input data; retain only type.
    name = type(error).__name__ if isinstance(error, BaseException) else 'ReportFailure'
    return {'schema': 'gamma.support-coverage-floor.report.v1', 'complete': False,
            'validation_loaded': False, 'failure_type': name, 'verdicts': None,
            'predictions': {'P1': None, 'P2': None},
            'm1_claim': False, 'packet_or_witness_claim': False}


def markdown(result):
    if result['complete'] is not True:return '# Item 56 incomplete\n\nNo verdict; incomplete execution or replay.\n'
    lines=['# Item 56 shared-only coverage floor','',
        'Every covering dictionary needs at least r one-owner entries on each fixed 300-source cohort. The 256-entry capacity is relaxed for this necessary condition. All 96 paid alphabet singletons are allowed here, so r equals the private-character-source count exactly; independent path replay cannot produce a stronger floor on these inputs.', '',
        '| Cohort | Coverage floor r | Private-character floor | Coverable by all shared entries | Item50 k* | Positive budgets below r | Positive budgets not ruled out |',
        '| --- | ---: | ---: | ---: | ---: | --- | --- |']
    for a in result['arms']:
        lines.append(f"| {a['cohort']} | {a['coverage_floor']} | {a['private_character_floor']} | {a['coverable_sources']} | {a['largest_positive_k']} | {a['positive_budgets_below_floor']} | {a['positive_budgets_not_ruled_out']} |")
    lines+=['','Predictions: '+json.dumps(result['predictions'],sort_keys=True), '',
        'k<r is coverage-infeasible, before fraction or capacity matters. k>=r is only not ruled out by this floor: it does not prove coverage, a256-entry dictionary, or10% character share. The floor is not a minimum achievable support budget.', '',
        SHARED,'','Production uses trie occurrences and prefix reachability; replay uses fresh AC occurrences and suffix reachability. Every prefix/suffix recurrence and exact source-success set is checked privately. Public output contains only aggregate counts and hashes.', '',
        'No q, seed,400-source carrier, validation, cases, source execution or witness packets. Only exact original item13 qualification is reused; item23 unchanged-source exit137 remains separate. No M1, semantic-reuse, fraction sufficiency, current-best or promotion claim.']
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


def combine(run,output,config,elapsed,returncodes):
    run,output=Path(run),Path(output);config_limits(config);number(elapsed,PHASE_SECONDS)
    assert not (output/'failure.json').exists()
    assert type(returncodes) is list and len(returncodes)==2 and all(type(v) is int and v==0 for v in returncodes)
    contract_hash=sha(HERE/'contract.json');production,supervisor=accepted_production(run,config,contract_hash)
    parents=parent50(config);arms=[]
    for cohort,raw in zip(COHORTS,production['arms']):
        assert not (output/(cohort+'-failure.json')).exists()
        a=read(output/(cohort+'.json'));expected=parents[cohort]
        assert set(a)==ARM_FIELDS and a['schema']=='gamma.support-coverage-floor.report-arm.v1'
        assert a['complete'] is True and a['validation_loaded'] is False and a['cohort']==cohort
        assert a['contract_sha256']==contract_hash and a['parent50_evidence_sha256']==config['parent50_evidence']['sha256']
        assert a['production_arm_sha256']==sha(run/cohort/'results.json')
        assert a['production_results_sha256']==sha(run/'results.json') and a['production_supervisor_sha256']==sha(run/'supervisor.json')
        assert a['bindings_sha256']==digest(raw['bindings'])
        checked_path=output/(cohort+'-proof.json');checked=read(checked_path)
        assert a['independent_proof_sha256']==sha(checked_path)
        proof_shape(checked,expected,{str(pid) for pid in config['fit_ids']},'suffix_reachable')
        for key in COMMON_FIELDS:exact(checked[key],raw['proof'][key])
        assert a['independent_suffix_sha256']==digest(checked['suffix_reachable'])
        for key,value in summary(raw['proof'],expected).items():exact(a[key],value)
        assert a['source_identity_sha256']==expected['source_identity_sha256']==digest(config['source_hashes'][cohort])
        assert a['banned_set_sha256']==expected['banned_set_sha256']
        paths=config['cohorts'][cohort]
        assert a['source_file_sha256']==raw['bindings']['source_sha256']==config['private_files'][paths['sources']]
        assert a['pool_file_sha256']==raw['bindings']['pool_sha256']==config['private_files'][paths['pool']]
        assert a['source_identity_sha256']==raw['bindings']['source_identity_sha256']
        assert a['banned_set_sha256']==raw['bindings']['banned_set_sha256']
        assert a['production_prefix_sha256']==digest(raw['proof']['prefix_reachable'])
        for key,value in a.items():
            if key.endswith('_sha256'):hash_string(value)
        assert a['production_phase_seconds_sha256']==digest(raw['phase_seconds'])
        exact(a['production_seconds'],raw['seconds']);exact(a['production_peak_rss_kib'],raw['peak_rss_kib'])
        number(a['report_worker_seconds'],min(WORKER_SECONDS,elapsed));integer(a['report_peak_rss_kib'],1,ADDRESS_SPACE_BYTES//1024)
        assert a['all_sources_independently_replayed'] is True and a['all_prefix_suffix_recurrences_checked'] is True
        assert a['shared_dependencies']==SHARED
        arms.append(a)
    predictions={'P1':True,'P2':all(a['largest_positive_k'] is not None and a['coverage_floor']>a['largest_positive_k'] for a in arms)}
    return {'schema':'gamma.support-coverage-floor.report.v1','complete':True,'validation_loaded':False,
        'contract_sha256':contract_hash,'parent50_evidence_sha256':config['parent50_evidence']['sha256'],
        'production_results_sha256':sha(run/'results.json'),'production_supervisor_sha256':sha(run/'supervisor.json'),
        'production_seconds':production['seconds'],'report_seconds':elapsed,'arms':arms,'predictions':predictions,
        'population':'fixed300_fit_only','scope':'Necessary support-budget coverage floor; all shared entries allowed,256-entry capacity relaxed.',
        'shared_dependencies':SHARED,'private_files_per_cohort':2,'q_or_seed_opened':False,'validation_or_cases_opened':False,
        'qualification':{'authority':'Exact original item13 source qualification reuse only','fresh_jobs':0,'new_witness_packets':0,
                         'inherited_failure':'Item23 unchanged-source exit137 remains separate.'},
        'feasibility_claim_at_or_above_floor':False,'minimum_support_claim':False,'m1_claim':False,'promotion_allowed':False,
        'packet_or_witness_claim':False}


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
        binding = module('support_coverage_floor_report_binding', HERE/'binding.py')
        config = read(HERE/'contract.json'); config_limits(config)
        binding.check_contract(config)
        contract_hash = sha(HERE/'contract.json')
        phase = 'production_receipts'
        production, supervisor = accepted_production(run, config, contract_hash)
        raw = next(arm for arm in production['arms'] if arm['cohort'] == cohort)
        phase = 'input_identity'
        inputs = binding.load_inputs(config, Path(work), cohort, effective)
        phase = 'fresh_independent_replay'
        checker = module('support_coverage_floor_report_checker', HERE/'coverage.py')
        proof_path = Path(output)/(cohort+'-proof.json')
        result = replay(cohort, inputs, raw, checker, config['parent50_arms'][cohort],proof_path)
        result.update(independent_proof_sha256=sha(proof_path),parent50_evidence_sha256=config['parent50_evidence']['sha256'],
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
