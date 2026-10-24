"""Auxiliary receipt-only diagnostics after completed item 42 independent replay.

No source/q loader, cardinality DP, assignment solver or optimization is called.
This file is outside the frozen execution inventory.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import tempfile
import time

HERE=Path(__file__).resolve().parent
LIT=HERE.parent
CONTRACT_SHA256='9a7e6f65d6f83fbe5727386824e0a13f863783cf70a406c365e1ccd1e2be8009'
SCALES=[[0,1],[1,4],[1,2],[1,1],[2,1],[4,1]]
SECONDS=120
MEMORY_BYTES=8*1024**3
if not __debug__ or os.environ.get('PYTHONOPTIMIZE','') not in ('','0'):
    raise RuntimeError('Receipt checks require normal Python assertions')


class Deadline(BaseException):pass


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.tmp');temp.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');temp.replace(path)


def finite(value,maximum):
    assert type(value) in (int,float) and math.isfinite(value) and 0<=value<=maximum


def minimum_edges(costs,cap):
    """Smallest k attaining the capped optimum; absence is positive infinity."""
    assert type(cap) is int and 1<=cap<=96 and costs[cap] is not None
    result=next(k for k in range(1,cap+1) if costs[k]==costs[cap])
    tight=result==cap
    assert tight==(costs[cap-1] is None or costs[cap]<costs[cap-1])
    return result,tight


def diagnose(receipt,summary):
    # Import the frozen pure checker, never its solver or cardinality routines.
    import proof
    assert set(receipt)=={'caps','unrestricted','assignments'}
    caps=receipt['caps'];unrestricted=receipt['unrestricted'];assignments=receipt['assignments']
    assert len(caps)==300 and set(caps)==set(unrestricted)
    for pid,values in caps.items():
        assert len(values)==97 and values[0] is None and type(unrestricted[pid]) is int
        previous=None
        for value in values[1:]:
            assert value is None or type(value) is int
            if previous is not None:assert value is not None and value<=previous
            if value is not None:assert value>=unrestricted[pid]
            previous=value
    necessary,exact=proof.verify_assignments(caps,unrestricted,assignments)
    path=sum(unrestricted.values());D=summary['denominator']
    assert type(D) is int and D>0
    assert summary['unrestricted_path_numerator']==path
    assert summary['necessary_path_numerator']==necessary and summary['joint_path_numerator']==exact
    assert summary['quantiles_feasible_in_relaxed_pool']==(exact is not None)
    top=summary['top_capacity_numerator'];assert type(top) is int and top>=0
    ceil=lambda n:-(-n//D)
    assert summary['unrestricted_numerator']==path-top and summary['unrestricted_integer_lower_bound']==ceil(path-top)
    assert summary['necessary_integer_lower_bound']==(None if necessary is None else ceil(necessary-top))
    assert summary['joint_numerator']==(None if exact is None else exact-top)
    assert summary['joint_integer_lower_bound']==(None if exact is None else ceil(exact-top))
    assert summary['joint_path_increase']==(None if exact is None else exact-path)
    assert summary['excludes_fixed300_joint_target']==(exact is None or exact-top>0)
    cases=assignments['median_cases']
    assert summary['feasible_median_cases']==sum(case['feasible'] for case in cases)
    minimizing=[a for a,case in enumerate(cases,1) if case['feasible'] and case['value']==exact]
    classes=[];tight_total=0
    if minimizing:
        first=minimizing[0];chosen=cases[first-1];ids=sorted(caps)
        for label,(name,cap,quota) in enumerate(zip(('lower_half','upper_middle','p95_remainder','unrestricted'),(first,64-first,96,None),(150,1,134,15))):
            positions=[i for i,x in enumerate(chosen['assignment']) if x==label];assert len(positions)==quota
            if cap is None:
                classes.append({'class':name,'assigned_programs':quota,'selection_cap':None,
                                'minimum_edges_histogram':None,'tight_programs':None,'tight_fraction':None})
                continue
            minima=[minimum_edges(caps[ids[i]],cap) for i in positions]
            tight=sum(flag for count,flag in minima);tight_total+=tight
            classes.append({'class':name,'assigned_programs':quota,'selection_cap':cap,
                            'minimum_edges_histogram':dict(sorted(Counter(str(count) for count,flag in minima).items(),key=lambda item:int(item[0]))),
                            'tight_programs':tight,'tight_fraction':tight/quota})
    assert bool(minimizing)==(exact is not None)
    return {'scale':summary['scale'],'denominator':D,'quantile_family_feasible':exact is not None,
            'all_minimizing_a':minimizing,'selected_a':minimizing[0] if minimizing else None,
            'assignment_rule':'Retained certified assignment at the smallest minimizing a; alternative optimal assignments are not enumerated.',
            'classes':classes,'capped_programs':285 if minimizing else None,
            'tight_capped_programs':tight_total if minimizing else None,
            'tight_capped_fraction':tight_total/285 if minimizing else None,
            'exact_minus_necessary_path_numerator':None if exact is None or necessary is None else exact-necessary,
            'necessary_minus_unrestricted_path_numerator':None if necessary is None else necessary-path,
            'exact_minus_unrestricted_path_numerator':None if exact is None else exact-path,
            'interpretation':'Minimum-edge tightness at this capped cost optimum, conditional on the retained assignment. Ties and reassignment can change counts; no causal attribution or primal witness.'}


def supervisor(receipt,phase,digest,limit,cleanup_limit):
    assert receipt['complete'] is True and receipt['phase']==phase and receipt['contract_sha256']==digest
    assert receipt['returncodes']==[0,0] and all(type(x) is int for x in receipt['returncodes'])
    finite(receipt['elapsed'],limit+cleanup_limit);finite(receipt['cleanup_seconds'],cleanup_limit)


def verified_inputs(run,main_report,expected_report_sha256):
    """Checks public/report authority before the caller can read point receipts."""
    contract_path=HERE/'contract.json';assert sha(contract_path)==CONTRACT_SHA256
    contract=read(contract_path)
    assert contract['active'] is True and contract['population']=='fixed300_fit_only' and contract['scales']==SCALES
    assert len(contract['code_hashes'])==121
    for rel,digest in contract['code_hashes'].items():assert sha(LIT/rel)==digest,rel
    for path,digest in contract['runtime_files'].items():assert sha(path)==digest,path
    parent_path=LIT/contract['parent_evidence'];assert sha(parent_path)==contract['code_hashes'][contract['parent_evidence']]
    parent=read(parent_path)
    assert parent['complete'] is True and parent['validation_loaded'] is False and parent['contract_sha256']==contract['parent_contract_sha256']
    assert sha(main_report/'results.json')==expected_report_sha256
    main=read(main_report/'results.json')
    assert main['schema']=='gamma.joint-quantile-fraction.report.v1' and main['complete'] is True
    assert main['population']=='fixed300_fit_only' and main['validation_loaded'] is False and main['contract_sha256']==CONTRACT_SHA256
    assert main['predictions']['P1'] is True
    assert not list(main_report.glob('*failure.json')) and not list(run.glob('*failure.json')) and not list(run.glob('*/*failure.json'))
    supervisor(read(main_report/'supervisor.json'),'report',CONTRACT_SHA256,contract['limits']['report_seconds'],contract['limits']['cleanup_seconds'])
    assert sha(run/'results.json')==main['private_results_sha256']
    raw=read(run/'results.json')
    assert raw['complete'] is True and raw['validation_loaded'] is False and raw['contract_sha256']==CONTRACT_SHA256
    supervisor(read(run/'supervisor.json'),'production',CONTRACT_SHA256,contract['limits']['production_seconds'],contract['limits']['cleanup_seconds'])
    finite(main['replay_seconds'],contract['limits']['report_seconds']);finite(raw['seconds'],contract['limits']['production_seconds'])
    assert main['production_seconds']==raw['seconds']
    assert [a['cohort'] for a in main['arms']]==[a['cohort'] for a in raw['arms']]==['R','naming']
    for arm,rawarm in zip(main['arms'],raw['arms']):
        cohort=arm['cohort'];assert arm==read(main_report/f'{cohort}.json')
        assert rawarm==read(run/cohort/'results.json')
        assert rawarm['complete'] is True and rawarm['validation_loaded'] is False
        assert arm['complete'] is True and arm['validation_loaded'] is False and arm['fit_problems']==300
        assert arm['independent_cardinality_assignment_and_pool_replay'] is True
        assert arm['source_sha256']==rawarm['source_sha256']==contract['private_files'][contract['sources'][cohort]]
        assert arm['parent_q_sha256']==rawarm['parent_q_sha256']==contract['private_files'][contract['parent_q'][cohort]]
        prior=next(p for p in parent['arms'] if p['cohort']==cohort)
        assert prior['fit_source_sha256']==arm['source_sha256'] and prior['certificate']['q_sha256']==arm['parent_q_sha256']
        assert prior['certificate']['independent_partition_and_integer_replay'] is True
        assert len(arm['points'])==len(rawarm['points'])==6
        for scale,point,old in zip(SCALES,arm['points'],rawarm['points']):
            assert point['scale']==old['scale']==scale and point['denominator']==contract['denominator']
            assert point['proof_sha256']==old['proof_sha256']
            assert all(point[k]==v for k,v in old.items() if k!='seconds')
    return main


def replay(run,main_report,expected_report_sha256):
    main=verified_inputs(run,main_report,expected_report_sha256);arms=[]
    for arm in main['arms']:
        points=[]
        for ordinal,summary in enumerate(arm['points']):
            path=run/arm['cohort']/f'point-{ordinal}.json'
            assert sha(path)==summary['proof_sha256']
            point=diagnose(read(path),summary);point['proof_sha256']=summary['proof_sha256'];points.append(point)
        arms.append({'cohort':arm['cohort'],'points':points})
    return {'schema':'gamma.joint-quantile-fraction.auxiliary.v1','complete':True,
            'contract_sha256':CONTRACT_SHA256,'main_report_sha256':expected_report_sha256,
            'private_results_sha256':main['private_results_sha256'],'auxiliary_script_sha256':sha(Path(__file__)),
            'validation_loaded':False,'source_or_q_loaded':False,'optimization_or_cardinality_dp_run':False,
            'promotion_allowed':False,'scope':'Receipt diagnostics only; fixed 300 fit sources, selections exclude Finish. Not M1 or a 400/500-program exclusion.',
            'arms':arms}


def withdraw(output,error):
    payload={'complete':False,'promotion_allowed':False,'diagnostics':None,'exception':type(error).__name__}
    items=[('results.json',json.dumps(payload,sort_keys=True,indent=2)+'\n'),
           ('REPORT.md','# Auxiliary quantile receipt diagnostics\n\nNo accepted diagnostics: prerequisite, receipt replay or publication failed. Any previous successful auxiliary conclusion is withdrawn.\n')]
    failed=[]
    for name,value in items:
        path=output/name
        try:
            output.mkdir(parents=True,exist_ok=True)
            temp=path.with_name(name+'.withdraw.tmp');temp.write_text(value);temp.replace(path)
        except BaseException:
            try:path.unlink(missing_ok=True)
            except BaseException:failed.append(name)
    if failed:raise OSError('Unable to withdraw auxiliary artifacts: '+','.join(failed)) from error


def publish(run,main_report,report_hash,output):
    started=time.monotonic()
    try:
        result=replay(run,main_report,report_hash)
        lines=['# Auxiliary quantile receipt diagnostics','',result['scope'],'',
               '| Cohort | q scale | Minimizing a values | Selected a | Tight capped / 285 | Exact − necessary path numerator | Necessary − unrestricted path numerator |',
               '| --- | --- | --- | ---: | ---: | ---: | ---: |']
        for arm in result['arms']:
            for p in arm['points']:
                lines.append(f"| {arm['cohort']} | {p['scale'][0]}/{p['scale'][1]} | {', '.join(map(str,p['all_minimizing_a'])) or 'infeasible'} | {p['selected_a']} | {p['tight_capped_programs']} | {p['exact_minus_necessary_path_numerator']} | {p['necessary_minus_unrestricted_path_numerator']} |")
        lines+=['','Path differences are exact numerators over the recorded denominator; they are not differences of rounded integer bounds. Each per-class histogram is in [metadata](results.json).','',
                'Tight means every path attaining that assigned capped optimum uses the cap number of selections. For a nontight class, some optimum uses fewer selections; longer tied optima may also exist. The uncapped 15-program class is excluded. Counts refer to the retained assignment at the smallest minimizing a; other optimum assignments are not enumerated. These diagnostics do not causally attribute a bound or produce a realizable dictionary witness.','']
        result['auxiliary_seconds']=time.monotonic()-started;finite(result['auxiliary_seconds'],SECONDS)
        output.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.aux-stage-',dir=output) as tmp:
            stage=Path(tmp);write(stage/'results.json',result);(stage/'REPORT.md').write_text('\n'.join(lines))
            finite(time.monotonic()-started,SECONDS)
            (stage/'REPORT.md').replace(output/'REPORT.md');(stage/'results.json').replace(output/'results.json')
        finite(time.monotonic()-started,SECONDS)
        return result
    except BaseException as error:
        withdraw(output,error)
        raise


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);parser.add_argument('--main-report',type=Path,required=True)
    parser.add_argument('--main-report-sha256',required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--core',type=int,choices=(4,5),default=4);args=parser.parse_args()
    assert args.output.resolve() not in (args.run.resolve(),args.main_report.resolve(),HERE.resolve())
    def expired(*_):raise Deadline('Auxiliary receipt-only deadline')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,SECONDS)
    try:
        os.sched_setaffinity(0,{args.core});resource.setrlimit(resource.RLIMIT_AS,(MEMORY_BYTES,)*2)
        publish(args.run,args.main_report,args.main_report_sha256,args.output)
        signal.setitimer(signal.ITIMER_REAL,0)
    except BaseException as error:
        signal.setitimer(signal.ITIMER_REAL,0);withdraw(args.output,error);raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)


if __name__=='__main__':main()
