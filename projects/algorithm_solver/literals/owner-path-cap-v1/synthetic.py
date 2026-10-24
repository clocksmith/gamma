"""Item57 supplied-input complexity harness; pinning is not run authorization."""
import time
STARTED=time.monotonic()
import signal
class HardDeadline(BaseException):pass
if __name__ == '__main__':
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(HardDeadline('Bootstrap deadline')))
    signal.setitimer(signal.ITIMER_REAL,180)
import argparse
import gc
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import unittest

HERE=Path(__file__).resolve().parent;LIT=HERE.parent;OLD=LIT/'potential-lift-certificate-v1';PARENT=LIT/'potential-tightening-v1'
SECONDS=180;EMERGENCY=10;MEMORY=8*1024**3
FILES=('DRAFT.md','DRAFT-NEXT.md','proof.py','test_proof.py','caps.py','test_caps.py',
       'independent.py','test_independent.py','synthetic.py','test_synthetic.py','SYNTHETIC-SPEC.md')
BASE_AGREE=('schema','lifted','tightened','new_only_class_counts','new_only_top_entries','digests','reductions','deltas')
AGREE=('schema','owner_caps','owner_top_entries','owner_entry_counts','owner_prefixes','capped_prefixes','one_owner_prefix','marginal_choices','shared_prefix','rows','deltas_vs53')


def checks():
    if not __debug__ or sys.flags.optimize or os.environ.get('PYTHONOPTIMIZE','') not in ('','0'):
        raise RuntimeError('Normal Python assertions required')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def write(path,value):
    path=Path(path);temporary=path.with_name(path.name+'.pending')
    temporary.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n');temporary.replace(path)


def original():
    spec=importlib.util.spec_from_file_location('potential53_original_fixture50',OLD/'synthetic.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def prepare():
    """Public invented-string metadata and pins only; no pool, q or kernel."""
    checks();old=original();parent=read(PARENT/'synthetic-spec.json');saved=read(PARENT/'synthetic-results.json')
    supervisor=read(PARENT/'synthetic-supervisor.json')
    assert saved['complete'] is True and saved['synthetic_only'] is True and saved['private_inputs_opened'] is False
    assert supervisor['complete'] is True and type(supervisor['exit_code']) is int and supervisor['exit_code']==0
    assert saved['spec_sha256']==supervisor['spec_sha256']==sha(PARENT/'synthetic-spec.json')
    assert 0<=saved['seconds']<=supervisor['seconds']<=180
    metadata=[old.fixture_metadata(*row) for row in old.fixtures()]
    assert metadata==parent['inputs']['fixtures']
    assert [r['name'] for r in saved['fixtures']]==[r['name'] for r in metadata]
    for got,expected in zip(saved['fixtures'],metadata):
        assert got['complete'] is True and got['independent_both257_agree'] is True
        assert all(got[key]==value for key,value in expected.items())
    code=dict(parent['code_hashes']);runtime=dict(parent['runtime_hashes'])
    for rel,h in code.items():assert sha(LIT/rel)==h,rel
    for path,h in runtime.items():assert sha(path)==h,path
    for path in [*(HERE/name for name in FILES),PARENT/'synthetic-spec.json',PARENT/'synthetic-results.json',PARENT/'synthetic-supervisor.json']:
        code[str(path.relative_to(LIT))]=sha(path)
    for module in (subprocess,resource,signal,unittest,importlib,hashlib,json,io,os,sys,gc,math,time):
        filename=getattr(module,'__file__',None)
        if filename:runtime[str(Path(filename).resolve())]=sha(Path(filename).resolve())
    runtime[str(Path(sys.executable).resolve())]=sha(Path(sys.executable).resolve())
    inputs=parent['inputs']
    return {'schema':'gamma.owner-path-cap.synthetic-spec.v1','synthetic_only':True,'private_inputs_opened':False,
        'core':6,'per_process_address_space_bytes':MEMORY,'whole_seconds':SECONDS,'emergency_seconds':EMERGENCY,
        'python_bin':str(Path(sys.executable).absolute()),'resolved_python_bin':str(Path(sys.executable).resolve()),
        'python_version':sys.version,'inputs':inputs,'input_spec_sha256':digest(inputs),
        'parent_spec_sha256':sha(PARENT/'synthetic-spec.json'),'parent_result_sha256':sha(PARENT/'synthetic-results.json'),
        'parent_supervisor_sha256':sha(PARENT/'synthetic-supervisor.json'),
        'code_hashes':code,'runtime_hashes':runtime,'oracle_modules':['test_proof','test_caps','test_independent'],
        'oracle_tests':15,
        'oracle_timing':'All15 before fixtures inside180s whole cap; imports/preflight also charged.',
        'old_timing_comparison':'Exact53 inputs/results comparison only; no matched total-time ratio.'}


def verify(expected):
    path=HERE/'synthetic-spec.json';assert sha(path)==expected,'Unexpected reviewed spec'
    value=read(path);assert prepare()==value,'Public code/runtime/invented input drift';return value


def arm(deadline):
    remaining=deadline-time.monotonic()
    if remaining<=0:raise HardDeadline('Absolute synthetic deadline')
    signal.setitimer(signal.ITIMER_REAL,remaining)


def resources():
    checks();os.sched_setaffinity(0,{6});resource.setrlimit(resource.RLIMIT_AS,(MEMORY,MEMORY))


def same(a,b):
    """Exact JSON identities, including dictionary keys and integer types."""
    assert type(a) is type(b),(type(a).__name__,type(b).__name__)
    if isinstance(a,dict):
        assert a.keys()==b.keys()
        for key in a:same(a[key],b[key])
    elif isinstance(a,(list,tuple)):
        assert len(a)==len(b)
        for x,y in zip(a,b):same(x,y)
    else:assert a==b


def compare(cert,checked,historical):
    for key in AGREE:same(cert[key],checked[key])
    for key in BASE_AGREE:same(cert['base'][key],checked['base'][key])
    common=set(cert['digests'])&set(checked['digests'])
    assert common==set(cert['digests'])-{'owner_prefix_schedule_sha256'}
    for key in common:same(cert['digests'][key],checked['digests'][key])
    assert checked['production_forward_schedule_checked'] is True
    assert checked['production_forward_schedule_sha256']==cert['digests']['owner_prefix_schedule_sha256']
    shape=checked['base']['geometry'];same(shape,historical['geometry'])
    same(checked['work']['production_forward_positions_checked'],shape['source_characters'])
    same(checked['work']['production_forward_endpoints_inspected'],cert['work']['schedule_endpoints_inspected'])
    same(checked['work']['schedule_occurrences_admitted'],cert['work']['schedule_one_owner_occurrences'])
    base=cert['base']
    for name,key in (('lifted','rows50'),('tightened','rows53')):same(base[name]['rows'],historical[key])
    for key in ('digests','reductions','deltas'):same(base[key],historical[key])
    same(base['new_only_class_counts'],{int(k):v for k,v in historical['new_only_class_counts'].items()})
    for key in ('old_charge','old_numerator','old_occurrences','occurrence_sha256'):same(base['lifted'][key],historical[key])
    same(base['lifted']['class_counts'],{int(k):v for k,v in historical['class_counts'].items()})
    same(sum(base['lifted']['path_numerators'].values()),historical['path_numerator'])
    assert len(cert['rows'])==len(cert['deltas_vs53'])==257
    for old,new,delta in zip(base['tightened']['rows'],cert['rows'],cert['deltas_vs53']):
        assert old['k']==new['k'] and new['charge']<=old['charge']
        same(delta,{'k':new['k'],'charge_reduction':old['charge']-new['charge'],
                    'integer_bound_gain':new['integer_lower_bound']-old['integer_lower_bound']})
    return {'independent_all257_agree':True,'historical53_saved_fields_agree':True,
        'independent_owner_top_identities_agree':True,'independent_base_paired_proofs_agree':True,
        'all_forward_recurrences_checked':True}


def oracles(names):
    class Result(unittest.TextTestResult):
        def addError(self,test,error):
            if issubclass(error[0],HardDeadline):raise error[1]
            super().addError(test,error)
    suite=unittest.defaultTestLoader.loadTestsFromNames(names)
    result=unittest.TextTestRunner(stream=io.StringIO(),resultclass=Result).run(suite)
    assert result.wasSuccessful(),'Supplied-input oracle failure'
    return result.testsRun


def worker(output,deadline,expected):
    assert type(deadline) in (int,float) and math.isfinite(deadline) and deadline<=STARTED+SECONDS
    resources();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(HardDeadline()))
    arm(deadline);config=verify(expected);old=original();historical=read(PARENT/'synthetic-results.json')
    import caps as p
    import independent
    receipt={'schema':'gamma.owner-path-cap.synthetic-result.v1','complete':False,
        'synthetic_only':True,'private_inputs_opened':False,'spec_sha256':expected,
        'input_spec_sha256':config['input_spec_sha256'],'fixtures':[],'phase':'oracles'}
    started=time.monotonic();begin=started
    receipt['oracle_tests']=oracles(config['oracle_modules']);assert receipt['oracle_tests']==config['oracle_tests']==15
    receipt['oracle_seconds']=time.monotonic()-begin
    for number,(name,texts,banned) in enumerate(old.fixtures()):
        arm(deadline);row=old.fixture_metadata(name,texts,banned);receipt['fixtures'].append(row)
        reference=historical['fixtures'][number];assert row['name']==reference['name']
        receipt['phase']=name+':pool';write(output/'worker-status.json',{'complete':False,'phase':receipt['phase']})
        begin=time.monotonic();pool=sorted(set(p.parent.full._suffix.build_pool(texts,banned))|set(old.ALPHABET))
        row.update(pool_seconds=time.monotonic()-begin,pool_entries=len(pool),pool_string_bytes=sum(len(x.encode()) for x in pool),pool_sha256=old.digest(pool))
        receipt['phase']=name+':q';begin=time.monotonic();q,transitions=old.generate_q(texts,pool)
        row.update(q_generation_seconds=time.monotonic()-begin,old_occurrences=len(q),q_generation_trie_transitions=transitions,q_sha256=old.digest(q))
        for key in ('pool_entries','pool_string_bytes','pool_sha256','old_occurrences','q_generation_trie_transitions','q_sha256'):
            same(row[key],reference[key])
        kwargs=dict(texts=texts,banned=banned,old_pool=pool,old_q=q,seed=old.ALPHABET,alphabet=old.ALPHABET,D=old.D,
                    expected_source_hashes=p.parent.source_hashes(texts),expected_old_banned=banned,capacity=256)
        receipt['phase']=name+':production';begin=time.monotonic();certificate=p.check(**kwargs)
        row['production_seconds']=time.monotonic()-begin
        assert certificate['base']['work']['old_trie_transitions']==transitions
        receipt['phase']=name+':independent_all_depth';begin=time.monotonic()
        checked=independent.check(**kwargs,expected_occurrence_sha256=certificate['base']['lifted']['occurrence_sha256'],
                                  expected_prefix_schedule=certificate['owner_prefix_schedule'])
        row['independent_seconds']=time.monotonic()-begin
        receipt['phase']=name+':comparison';begin=time.monotonic();row.update(compare(certificate,checked,reference))
        base=certificate['base'];shape=checked['base']['geometry']
        row.update(comparison_seconds=time.monotonic()-begin,geometry=shape,denominator=old.D,
            path_numerator=sum(base['lifted']['path_numerators'].values()),old_charge=base['lifted']['old_charge'],
            old_numerator=base['lifted']['old_numerator'],occurrence_sha256=base['lifted']['occurrence_sha256'],
            class_counts=base['lifted']['class_counts'],rows50=base['lifted']['rows'],rows53=base['tightened']['rows'],
            rows57=certificate['rows'],deltas_vs53=certificate['deltas_vs53'],base_digests=base['digests'],
            digests=certificate['digests'],independent_digests=checked['digests'],owner_caps=certificate['owner_caps'],
            owner_entry_counts=certificate['owner_entry_counts'],
            production_work=certificate['work'],independent_work=checked['work'],
            base_production_work=base['work'],base_independent_work=checked['base']['work'],
            strict_charge_budgets=sum(d['charge_reduction']>0 for d in certificate['deltas_vs53']),
            strict_integer_budgets=sum(d['integer_bound_gain']>0 for d in certificate['deltas_vs53']),
            peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            memory_scope='Cumulative worker peak; not incremental per fixture or summed across processes.',complete=True)
        if number==0:assert row['production_work']['owner_unique_entries_extracted']>0
        else:assert row['production_work']['repeated_new_occurrence_contributions']>0
        write(output/'worker-status.json',{'complete':False,'phase':name+':checked','completed_fixtures':number+1})
        del q,pool,certificate,checked,texts,banned,kwargs,base;gc.collect()
    arm(deadline);receipt.update(complete=True,phase='complete',worker_seconds=time.monotonic()-STARTED,
        computation_seconds=time.monotonic()-started,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write(output/'worker-results.json',receipt);arm(deadline)


def command(output,deadline,expected):
    return [sys.executable,'-B',str(HERE/'synthetic.py'),'--worker','--output',str(output),
            '--deadline',str(deadline),'--spec-sha256',expected]


def remove_success(output,deadline):
    for name in ('results.json','supervisor.json','REPORT.md'):
        arm(deadline)
        try:(output/name).unlink(missing_ok=True)
        except OSError:pass


def kill(process,deadline):
    if process is None:return
    arm(deadline)
    try:os.killpg(process.pid,signal.SIGKILL)
    except ProcessLookupError:pass


def stop(process,deadline):
    if process is None:return
    kill(process,deadline)
    arm(deadline);process.wait(timeout=max(.001,deadline-time.monotonic()))


def withdraw(output,failure,deadline):
    remove_success(output,deadline)
    for name in ('failure.json','results.json','supervisor.json'):
        arm(deadline)
        try:write(output/name,failure)
        except HardDeadline:raise
        except Exception:
            arm(deadline)
            try:(output/name).unlink(missing_ok=True)
            except OSError:pass
    arm(deadline)
    (output/'REPORT.md').write_text('# Item57 synthetic incomplete\n\nNo accepted complexity comparison.\n')
    arm(deadline)


def main(output,expected):
    deadline=STARTED+SECONDS;phase='preflight';process=None;log=None;writable=False;cleanup_started=None
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(HardDeadline()))
    try:
        arm(deadline);resources();config=verify(expected)
        assert not output.exists(),'Fresh output required; existing results preserved'
        output.mkdir(parents=True);writable=True
        write(output/'supervisor.json',{'complete':False,'phase':'preflight','synthetic_only':True})
        log=(output/'worker.log').open('xb');phase='worker';arm(deadline)
        process=subprocess.Popen(command(output,deadline,expected),stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
            env=dict(os.environ,PYTHONHASHSEED='0',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
        process.wait(timeout=max(.001,deadline-time.monotonic()))
        assert type(process.returncode) is int and process.returncode==0,'Synthetic worker failed'
        phase='collect';arm(deadline);result=read(output/'worker-results.json')
        assert result['complete'] is True and result['spec_sha256']==expected and result['input_spec_sha256']==config['input_spec_sha256']
        assert [row['name'] for row in result['fixtures']]==[row['name'] for row in config['inputs']['fixtures']]
        assert len(result['fixtures'])==2 and all(row['complete'] is True and row['independent_all257_agree'] is True and row['historical53_saved_fields_agree'] is True and row['all_forward_recurrences_checked'] is True for row in result['fixtures'])
        assert all(type(result[k]) in (int,float) and math.isfinite(result[k]) and 0<=result[k]<=SECONDS for k in ('worker_seconds','computation_seconds','oracle_seconds'))
        phase='cleanup';cleanup_started=time.monotonic();cleanup_deadline=min(deadline,cleanup_started+EMERGENCY)
        kill(process,cleanup_deadline);remove_success(output,cleanup_deadline);stop(process,cleanup_deadline)
        arm(cleanup_deadline);log.close();log=None;arm(cleanup_deadline)
        cleanup_seconds=time.monotonic()-cleanup_started
        phase='publication';arm(deadline)
        result.update(seconds=time.monotonic()-STARTED,normal_cleanup_seconds=cleanup_seconds,
            supervisor_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            memory_scope='Worker and supervisor peaks are separate, not simultaneous or an aggregate8GiB cap.')
        temporary=output/'REPORT.md.pending';temporary.write_text('# Item57 supplied-input complexity\n\nBoth fixed invented fixtures independently reconcile all257 budgets for50/53/57 and every forward scheduling recurrence.\n\nMetadata and complete curves: results.json. No corpus runtime estimate or scientific claim.\n');temporary.replace(output/'REPORT.md')
        arm(deadline);write(output/'supervisor.json',{'complete':True,'synthetic_only':True,'spec_sha256':expected,
            'seconds':time.monotonic()-STARTED,'normal_cleanup_seconds':cleanup_seconds,'exit_code':process.returncode})
        arm(deadline);write(output/'results.json',result);arm(deadline)
        return result
    except BaseException as error:
        signal.setitimer(signal.ITIMER_REAL,0)
        first=cleanup_started if phase=='cleanup' and cleanup_started is not None else time.monotonic()
        emergency=min(first+EMERGENCY,deadline+EMERGENCY)
        failure={'complete':False,'synthetic_only':True,'private_inputs_opened':False,'phase':phase,
            'error_type':type(error).__name__,'spec_sha256':expected,'seconds':time.monotonic()-STARTED,
            'comparison_accepted':False}
        try:
            if process is not None:
                arm(emergency)
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
            if writable:remove_success(output,emergency)
            stop(process,emergency)
            if log is not None:arm(emergency);log.close();log=None
        except BaseException as cleanup_error:failure['cleanup_error_type']=type(cleanup_error).__name__
        try:
            arm(emergency)
            if writable:withdraw(output,failure,emergency)
        except HardDeadline:pass
        finally:signal.setitimer(signal.ITIMER_REAL,0)
        raise RuntimeError('Synthetic comparison incomplete; no accepted result') from error
    finally:signal.setitimer(signal.ITIMER_REAL,0)


if __name__=='__main__':
    ap=argparse.ArgumentParser();mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--pin',action='store_true');mode.add_argument('--run',action='store_true');mode.add_argument('--worker',action='store_true')
    ap.add_argument('--output',type=Path);ap.add_argument('--spec-sha256');ap.add_argument('--deadline',type=float)
    args=ap.parse_args()
    if args.pin:
        value=prepare();write(HERE/'synthetic-spec.json',value)
        print(json.dumps({'prepared_only':True,'sha256':sha(HERE/'synthetic-spec.json'),'input_spec_sha256':value['input_spec_sha256']}))
    else:
        if args.output is None or args.spec_sha256 is None:ap.error('--output and --spec-sha256 required')
        if args.worker:
            assert args.deadline is not None and math.isfinite(args.deadline)
            worker(args.output.resolve(),args.deadline,args.spec_sha256)
        else:main(args.output.resolve(),args.spec_sha256)
