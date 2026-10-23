"""Independent fixed-population replay and metadata-only publication."""
import argparse
import json
import os
from pathlib import Path
import resource
import signal
import time
import common as c


def verify_run(raw,contract):
    assert set(raw)=={'complete','validation_loaded','contract_sha256','seconds','arms'}
    assert raw['complete'] is True and raw['validation_loaded'] is False
    assert raw['contract_sha256']==c.sha(c.HERE/'contract.json')
    elapsed=c.number(raw['seconds'],contract['limits']['production_seconds'])
    assert len(raw['arms'])==2 and [a['cohort'] for a in raw['arms']]==['R','naming']
    for a in raw['arms']:c.number(a['seconds'],elapsed)


def verify_supervisor(receipt,raw,contract):
    assert set(receipt)=={'complete','phase','contract_sha256','elapsed','cleanup_seconds','returncodes'}
    assert receipt['complete'] is True and receipt['phase']=='production'
    assert receipt['contract_sha256']==raw['contract_sha256']
    assert receipt['returncodes']==[0,0] and all(type(v) is int for v in receipt['returncodes'])
    cleanup=c.number(receipt['cleanup_seconds'],contract['limits']['cleanup_seconds'])
    elapsed=c.number(receipt['elapsed'],contract['limits']['production_seconds']+contract['limits']['cleanup_seconds'])
    assert raw['seconds']<=elapsed and cleanup<=elapsed


def replay_arm(cohort,work,run,output,deadline):
    c.mechanism.parent.require_checks();started=time.monotonic();phase='preflight'
    contract=json.loads((c.HERE/'contract.json').read_text())
    def expired(*_):raise TimeoutError('whole-report deadline')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,max(.001,deadline-started))
    try:
        assert 0<deadline-started<=contract['limits']['report_seconds']
        os.sched_setaffinity(0,set(contract['limits']['arm_cores'][cohort]))
        resource.setrlimit(resource.RLIMIT_AS,(contract['limits']['address_space_bytes'],)*2)
        c.check_contract(contract,work)
        assert not (run/'failure.json').exists() and not list(run.glob('*/failure.json'))
        raw=json.loads((run/'results.json').read_text());verify_run(raw,contract)
        verify_supervisor(json.loads((run/'supervisor.json').read_text()),raw,contract)
        arm=next(a for a in raw['arms'] if a['cohort']==cohort)
        assert arm==json.loads((run/cohort/'results.json').read_text())
        assert set(arm)=={'cohort','complete','validation_loaded','points','counts','source_sha256','parent_q_sha256','contract_sha256','seconds','peak_rss_kib'}
        assert arm['complete'] is True and arm['validation_loaded'] is False
        assert arm['contract_sha256']==raw['contract_sha256']
        assert type(arm['peak_rss_kib']) is int and 0<arm['peak_rss_kib']<=contract['limits']['address_space_bytes']//1024
        assert arm['source_sha256']==contract['private_files'][contract['sources'][cohort]]
        assert arm['parent_q_sha256']==contract['private_files'][contract['parent_q'][cohort]]
        assert len(arm['points'])==len(c.SCALES)
        phase='index';index,parent_q,prior,counts=c.load_cohort(contract,work,cohort)
        assert arm['counts']==counts
        ends=c.mechanism.parent.independently_relocate_bans(index.base)
        assert ends==index.base.banned_ends
        D=contract['denominator'];points=[]
        for ordinal,(scale,old) in enumerate(zip(c.SCALES,arm['points'])):
            phase=f'point_{ordinal}';clock=time.monotonic();q=c.scaled(parent_q,scale)
            path=run/cohort/f'point-{ordinal}.json';assert c.sha(path)==old['proof_sha256']
            receipt=json.loads(path.read_text());assert set(receipt)=={'caps','unrestricted','assignments'}
            # The inherited verifier independently checks all pool pieces,
            # exact multiplicity top selection, bans and unrestricted paths.
            unrestricted_numerator=c.mechanism.parent.verify(index,q,256,D)
            unrestricted_certificate=index.certificate(q,256,D)
            assert unrestricted_numerator==unrestricted_certificate['numerator']
            unrestricted=unrestricted_certificate['path_numerators']
            assert receipt['unrestricted']==unrestricted
            caps=c.proof.tree_caps(index.texts,q,D,ends)
            assert receipt['caps']==caps
            summary=c.scalar_result(scale,q,caps,unrestricted,receipt['assignments'],unrestricted_certificate['top_capacity_numerator'],D)
            assert set(old)==set(summary)|{'proof_sha256','seconds'}
            assert all(old[k]==v for k,v in summary.items())
            c.number(old['seconds'],arm['seconds'])
            if scale==(1,1):c.check_parent_point(summary,unrestricted,prior)
            summary.update(proof_sha256=c.sha(path),production_seconds=old['seconds'],replay_seconds=time.monotonic()-clock)
            points.append(summary)
        assert sum(p['production_seconds'] for p in points)<=arm['seconds']
        # An empty exact quantile family is a separately certified exclusion.
        selected=max(range(len(points)),key=lambda i:(not points[i]['quantiles_feasible_in_relaxed_pool'],
                     points[i]['joint_numerator'] if points[i]['joint_numerator'] is not None else 0,-i))
        assert len({p['quantiles_feasible_in_relaxed_pool'] for p in points})==1
        result={'cohort':cohort,'complete':True,'validation_loaded':False,'fit_problems':300,
                'source_sha256':arm['source_sha256'],'parent_q_sha256':arm['parent_q_sha256'],'counts':counts,
                'points':points,'selected_point':selected,'selected_scale':points[selected]['scale'],
                'excludes_fixed300_joint_target':points[selected]['excludes_fixed300_joint_target'],
                'independent_cardinality_assignment_and_pool_replay':True,
                'production_seconds':arm['seconds'],'production_peak_rss_kib':arm['peak_rss_kib'],
                'replay_seconds':time.monotonic()-started,'replay_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        c.number(result['replay_seconds'],contract['limits']['report_seconds']);c.write(output/f'{cohort}.json',result)
    except BaseException as error:
        c.write(output/f'{cohort}-failure.json',{'complete':False,'phase':phase,'exception':type(error).__name__,
                'seconds':time.monotonic()-started,'partial_certificates_promoted':False});raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)


def publish(result,output):
    c.write(output/'results.json',result)
    lines=['# Fixed-300 joint selection-quantile and fraction certificate','',
           'Population: the named 300 fit sources only. N counts selections excluding Finish; actions=N+1.',
           'This report excludes neither M1 nor any 400/500-program target. No feasible witness or source qualification is produced.','']
    if result['complete']:
        lines+=['All twelve fixed points completed and independently replayed.','',
                '| Cohort | q scale | Unrestricted F lower | Necessary-quantile F lower | Exact-median/p95 F lower | Excludes fixed-300 joint target |',
                '| --- | --- | ---: | ---: | ---: | --- |']
        for arm in result['arms']:
            for p in arm['points']:
                exact=p['joint_integer_lower_bound'] if p['quantiles_feasible_in_relaxed_pool'] else 'No quantile-feasible relaxed paths'
                lines.append(f"| {arm['cohort']} | {p['scale'][0]}/{p['scale'][1]} | {p['unrestricted_integer_lower_bound']} | {p['necessary_integer_lower_bound']} | {exact} | {p['excludes_fixed300_joint_target']} |")
        lines+=['','Nonpositive bounds are inconclusive. Conditional bounds have no reported gap to an unqualified seed encoding.','',
                '| Prediction | Outcome |','| --- | --- |']
        lines += [f'| {k} | {v} |' for k,v in result['predictions'].items()]
    else:lines+=['Incomplete: no overall certificate or numerical verdict accepted. Failure receipts are retained.']
    (output/'REPORT.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--cohort',choices=('R','naming'),required=True)
    ap.add_argument('--work',type=Path,required=True);ap.add_argument('--run',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--deadline',type=float,required=True)
    a=ap.parse_args();replay_arm(a.cohort,a.work,a.run,a.output,a.deadline)
