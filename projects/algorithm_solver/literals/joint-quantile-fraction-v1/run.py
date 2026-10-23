"""Activated six-point exact-cap worker; no optimizer or witness generation."""
import argparse
import json
import os
from pathlib import Path
import resource
import signal
import time
import common as c


def arm(cohort,work,output,deadline):
    c.mechanism.parent.require_checks();started=time.monotonic();phase='preflight'
    contract=json.loads((c.HERE/'contract.json').read_text());folder=output/cohort;folder.mkdir()
    def expired(*_):raise TimeoutError('whole-job deadline')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,max(.001,deadline-started))
    try:
        assert 0<deadline-started<=contract['limits']['production_seconds']
        os.sched_setaffinity(0,set(contract['limits']['arm_cores'][cohort]))
        resource.setrlimit(resource.RLIMIT_AS,(contract['limits']['address_space_bytes'],)*2)
        c.check_contract(contract,work);phase='index'
        index,parent_q,prior,counts=c.load_cohort(contract,work,cohort);D=contract['denominator'];points=[]
        for ordinal,scale in enumerate(c.SCALES):
            phase=f'point_{ordinal}';clock=time.monotonic();q=c.scaled(parent_q,scale)
            c.mechanism.parent.validate_q(index.texts,q,256,D)
            caps=c.mechanism.exact_caps(index.texts,q,D,index.base.banned_ends)
            unrestricted=c.mechanism.parent.heap_paths(index.texts,q,D,index.base.banned_ends)
            top,_=index.weighted_selection(q,256)
            assignments=c.proof.build_assignments(caps,unrestricted)
            summary=c.scalar_result(scale,q,caps,unrestricted,assignments,top,D)
            if scale==(1,1):c.check_parent_point(summary,unrestricted,prior)
            witness={'caps':caps,'unrestricted':unrestricted,'assignments':assignments}
            path=folder/f'point-{ordinal}.json';c.write(path,witness)
            summary.update(proof_sha256=c.sha(path),seconds=time.monotonic()-clock)
            points.append(summary)
            c.write(folder/'progress.json',{'cohort':cohort,'complete':False,'points_completed':len(points),'seconds':time.monotonic()-started})
        result={'cohort':cohort,'complete':True,'validation_loaded':False,'points':points,'counts':counts,
                'source_sha256':contract['private_files'][contract['sources'][cohort]],
                'parent_q_sha256':contract['private_files'][contract['parent_q'][cohort]],
                'contract_sha256':c.sha(c.HERE/'contract.json'),'seconds':time.monotonic()-started,
                'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        c.number(result['seconds'],contract['limits']['production_seconds']);c.write(folder/'results.json',result)
    except BaseException as error:
        c.write(folder/'failure.json',{'complete':False,'phase':phase,'exception':type(error).__name__,
                'seconds':time.monotonic()-started,'partial_certificates_promoted':False});raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--cohort',choices=('R','naming'),required=True)
    ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--deadline',type=float,required=True);a=ap.parse_args();arm(a.cohort,a.work,a.output,a.deadline)
