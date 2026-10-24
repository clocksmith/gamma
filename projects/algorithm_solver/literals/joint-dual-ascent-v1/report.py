"""Independent certificates at zero/final best; trajectory values are diagnostics."""
import argparse
import json
import os
from pathlib import Path
import resource
import signal
import tempfile
import time
import common as c
import production


def replay_point(index,q,stored,contract):
    D=contract['denominator'];c.p.dual.validate_q(index.texts,q,256,D)
    assert set(stored)=={'numerator','denominator','joint_path_numerator','top_capacity_numerator','selected_a','assignments'}
    assert stored['denominator']==D
    ends=c.p.dual.independently_relocate_bans(index.base);assert ends==index.base.banned_ends
    unrestricted_bound=c.p.dual.verify(index,q,256,D)
    unrestricted=c.p.dual.heap_paths(index.texts,q,D,ends)
    top=sum(unrestricted.values())-unrestricted_bound
    caps=c.p.assignment.tree_caps(index.texts,q,D,ends)
    assert len(caps)==300 and len(stored['assignments'])==32
    values=[];ids=sorted(caps)
    for a,receipt in enumerate(stored['assignments'],1):
        costs=[[caps[p][a],caps[p][64-a],caps[p][96],unrestricted[p]] for p in ids]
        value=c.p.assignment.verify_assignment(costs,[150,1,134,15],receipt)
        if value is not None:values.append((value,a))
    assert values,'Parent joint family unexpectedly infeasible'
    path,a=min(values)
    assert stored['selected_a']==a and stored['joint_path_numerator']==path
    assert stored['top_capacity_numerator']==top and stored['numerator']==path-top
    return {'numerator':path-top,'denominator':D,'integer_lower_bound':-(-(path-top)//D),
            'joint_path_numerator':path,'top_capacity_numerator':top,'selected_a':a,
            'all_minimizing_a':[case for value,case in values if value==path],
            'full_pool_cardinality_and_assignment_replay':True,'excludes_fixed300_joint_target':path-top>0}


def verify_trajectory(arm,contract):
    rows=arm['trajectory_search_diagnostics'];assert 1<=len(rows)<=contract['search']['points']
    best=None
    for ordinal,row in enumerate(rows):
        assert set(row)=={'iteration','q_digest','numerator_search_only','selected_a_search_only','gradient_squared_norm','step','projected_movement','retained_best','endpoint_peak_bytes','phase_seconds','seconds'}
        assert type(row['iteration']) is int and row['iteration']==ordinal
        assert type(row['numerator_search_only']) is int and type(row['selected_a_search_only']) is int and 1<=row['selected_a_search_only']<=32
        assert type(row['gradient_squared_norm']) is int and row['gradient_squared_norm']>=0
        assert row['step']==production.step(contract['denominator'],ordinal)
        assert type(row['endpoint_peak_bytes']) is int and 0<row['endpoint_peak_bytes']<=contract['limits']['endpoint_bytes']
        assert type(row['q_digest']) is str and len(row['q_digest'])==64 and all(ch in '0123456789abcdef' for ch in row['q_digest'])
        c.number(row['seconds'],arm['seconds'])
        assert set(row['phase_seconds'])=={'cardinality_and_unrestricted','all_assignments','dictionary_weights_and_multiplicity','path_recovery_and_gradient'}
        for value in row['phase_seconds'].values():c.number(value,row['seconds'])
        assert sum(row['phase_seconds'].values())<=row['seconds']+.01
        improve=best is None or row['numerator_search_only']>best['numerator']
        assert type(row['retained_best']) is bool and row['retained_best']==improve
        if improve:best={'numerator':row['numerator_search_only'],'iteration':ordinal,'q_digest':row['q_digest']}
        if ordinal+1<len(rows):assert row['projected_movement'] is True and row['gradient_squared_norm']>0
    assert arm['best']==best and sum(r['seconds'] for r in rows)<=arm['seconds']+.01
    last=rows[-1]
    if arm['stop']=='point_limit':assert len(rows)==contract['search']['points'] and last['projected_movement'] is None
    elif arm['stop']=='zero_supergradient':assert last['gradient_squared_norm']==0 and last['projected_movement'] is None
    elif arm['stop']=='unchanged_projection':assert last['gradient_squared_norm']>0 and last['projected_movement'] is False
    else:raise AssertionError('Unregistered early stop')


def replay_arm(cohort,work,run,output,deadline):
    started=time.monotonic();phase='preflight'
    def expired(*_):raise c.HardDeadline('Whole independent-report deadline')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,max(.001,min(1200,deadline-started)))
    try:
        contract=c.read(c.HERE/'contract.json');assert contract['limits']['report_seconds']==1200 and 0<deadline-started<=1200
        os.sched_setaffinity(0,set(contract['limits']['arm_cores'][cohort]));resource.setrlimit(resource.RLIMIT_AS,(contract['limits']['address_space_bytes'],)*2)
        c.check(contract)
        assert not list(run.glob('*failure.json')) and not list(run.glob('*/*failure.json'))
        raw=c.read(run/'results.json');supervisor=c.read(run/'supervisor.json')
        assert raw['complete'] is True and raw['validation_loaded'] is False and raw['contract_sha256']==c.sha(c.HERE/'contract.json')
        assert supervisor['complete'] is True and supervisor['phase']=='production' and supervisor['returncodes']==[0,0]
        assert all(type(x) is int for x in supervisor['returncodes']) and supervisor['contract_sha256']==raw['contract_sha256']
        c.number(raw['seconds'],contract['limits']['production_seconds'])
        c.number(supervisor['elapsed'],contract['limits']['production_seconds']+contract['limits']['cleanup_seconds'])
        c.number(supervisor['cleanup_seconds'],contract['limits']['cleanup_seconds']);assert raw['seconds']<=supervisor['elapsed']
        assert [a['cohort'] for a in raw['arms']]==['R','naming']
        arm=next(a for a in raw['arms'] if a['cohort']==cohort);assert arm==c.read(run/cohort/'results.json')
        assert set(arm)=={'trajectory_search_diagnostics','best','stop','cohort','complete','validation_loaded','parent_q_loaded','counts','source_sha256','contract_sha256','targets','seconds','peak_rss_kib'}
        assert arm['complete'] is True and arm['validation_loaded'] is False and arm['parent_q_loaded'] is False
        assert arm['contract_sha256']==raw['contract_sha256'] and set(arm['targets'])=={'zero','best'}
        c.number(arm['seconds'],raw['seconds']);assert type(arm['peak_rss_kib']) is int and 0<arm['peak_rss_kib']<=contract['limits']['address_space_bytes']//1024
        assert arm['source_sha256']==contract['private_files'][contract['sources'][cohort]]
        verify_trajectory(arm,contract);phase='index';index,counts=c.load(contract,work,cohort);assert counts==arm['counts']
        targets={};cache={}
        for name in ('zero','best'):
            phase=name;spec=arm['targets'][name];qfile=run/cohort/f'{name}-q.json';proof_file=run/cohort/f'{name}-proof.json'
            assert set(spec)=={'q_sha256','proof_sha256'} and c.sha(qfile)==spec['q_sha256'] and c.sha(proof_file)==spec['proof_sha256']
            q=c.read(qfile);stored=c.read(proof_file)
            row=arm['trajectory_search_diagnostics'][0 if name=='zero' else arm['best']['iteration']]
            assert c.digest(q)==row['q_digest'] and stored['numerator']==row['numerator_search_only']
            assert stored['selected_a']==row['selected_a_search_only']
            if name=='zero':assert all(v==0 for rows in q.values() for row in rows for v in row)
            key=(spec['q_sha256'],spec['proof_sha256'])
            if key not in cache:cache[key]=replay_point(index,q,stored,contract)
            targets[name]={**cache[key],**spec,'q_digest':c.digest(q)}
        assert targets['zero']['numerator']==contract['baseline_numerators'][cohort]
        assert targets['best']['numerator']>=targets['zero']['numerator'] and targets['best']['numerator']==arm['best']['numerator']
        result={'cohort':cohort,'complete':True,'validation_loaded':False,'parent_q_loaded':False,'fit_problems':300,
                'source_sha256':arm['source_sha256'],'counts':counts,'targets':targets,
                'best_iteration':arm['best']['iteration'],'stop':arm['stop'],
                'trajectory_search_diagnostics':arm['trajectory_search_diagnostics'],
                'trajectory_scope':'Only zero/final-best targets are independently certified; other trajectory objectives and gradients are search diagnostics.',
                'production_seconds':arm['seconds'],'production_peak_rss_kib':arm['peak_rss_kib'],
                'replay_seconds':time.monotonic()-started,'replay_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        c.number(result['replay_seconds'],contract['limits']['report_seconds']);c.write(output/f'{cohort}.json',result)
    except BaseException as error:
        (output/f'{cohort}.json').unlink(missing_ok=True)
        c.write(output/f'{cohort}-failure.json',{'complete':False,'phase':phase,'exception':type(error).__name__,'partial_best_accepted':False});raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)


def publish(result,output):
    """Stage both report files; every publication error withdraws stale success."""
    try:
        lines=['# Joint conditional dual ascent','',
               'Same named 300 fit sources only. Selections exclude Finish. These bounds exclude neither M1 nor a 400/500-program target. No primal upper bound, witness or optimality claim.','']
        if result['complete']:
            lines+=['| Cohort | q=0 F lower | Final-best F lower | Best iteration | Positive exclusion |','| --- | ---: | ---: | ---: | --- |']
            for a in result['arms']:
                z,b=a['targets']['zero'],a['targets']['best'];lines.append(f"| {a['cohort']} | {z['integer_lower_bound']} | {b['integer_lower_bound']} | {a['best_iteration']} | {b['excludes_fixed300_joint_target']} |")
            lines+=['','Both retained targets are independently verified using full-pool and segment-tree cardinality replay plus exact assignment primal/dual checks. Other trajectory values remain search diagnostics. Nonpositive bounds are inconclusive. No convergence claim follows from the finite integer schedule.','',
                    'Predictions: '+', '.join(f'{k}={v}' for k,v in result['predictions'].items())+'.']
        else:lines+=['**No verdict.** Incomplete execution, verification or publication withdraws any earlier conclusion.']
        output.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.report-stage-',dir=output) as tmp:
            stage=Path(tmp);c.write(stage/'results.json',result);(stage/'REPORT.md').write_text('\n'.join(lines)+'\n')
            (stage/'REPORT.md').replace(output/'REPORT.md');(stage/'results.json').replace(output/'results.json')
    except BaseException as error:
        withdraw(output,error);raise


def withdraw(output,error):
    failure={'complete':False,'validation_loaded':False,'partial_best_accepted':False,'exception':type(error).__name__}
    failed=[]
    for name,text in [('results.json',json.dumps(failure)+'\n'),('REPORT.md','# Joint conditional dual ascent\n\n**No verdict.** Prior successful conclusions are withdrawn after an execution, verification or publication failure.\n')]:
        path=output/name
        try:output.mkdir(parents=True,exist_ok=True);path.write_text(text)
        except BaseException:
            try:path.unlink(missing_ok=True)
            except BaseException:failed.append(name)
    if failed:raise OSError('Failed to withdraw '+','.join(failed)) from error


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--cohort',choices=('R','naming'),required=True);ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--run',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--deadline',type=float,required=True);a=ap.parse_args()
    replay_arm(a.cohort,a.work,a.run,a.output,a.deadline)
