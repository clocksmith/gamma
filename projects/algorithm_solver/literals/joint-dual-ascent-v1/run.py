"""Activated source-only worker; all search inputs are the named fixed fit cohort."""
import argparse
import os
from pathlib import Path
import resource
import signal
import time
import common as c
import production


def arm(cohort,work,output,deadline):
    started=time.monotonic();folder=output/cohort;phase='preflight'
    def expired(*_):raise c.HardDeadline('Whole production deadline')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,max(.001,min(1200,deadline-started)))
    try:
        contract=c.read(c.HERE/'contract.json');assert contract['limits']['production_seconds']==1200 and 0<deadline-started<=1200
        os.sched_setaffinity(0,set(contract['limits']['arm_cores'][cohort]));resource.setrlimit(resource.RLIMIT_AS,(contract['limits']['address_space_bytes'],)*2)
        c.check(contract);folder.mkdir();phase='index';index,counts=c.load(contract,work,cohort)
        def save(name,q,proof):
            if q is not None:c.write(folder/f'{name}-q.json',q)
            c.write(folder/('progress.json' if name=='progress' else f'{name}-proof.json'),proof)
        phase='search';result=production.search(index,contract,contract['baseline_numerators'][cohort],save)
        result.update(cohort=cohort,complete=True,validation_loaded=False,parent_q_loaded=False,counts=counts,
                      source_sha256=contract['private_files'][contract['sources'][cohort]],contract_sha256=c.sha(c.HERE/'contract.json'),
                      targets={name:{'q_sha256':c.sha(folder/f'{name}-q.json'),'proof_sha256':c.sha(folder/f'{name}-proof.json')} for name in ('zero','best')},
                      seconds=time.monotonic()-started,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        c.number(result['seconds'],contract['limits']['production_seconds']);c.write(folder/'results.json',result)
    except BaseException as error:
        c.write(folder/'failure.json',{'complete':False,'phase':phase,'exception':type(error).__name__,'seconds':time.monotonic()-started,'partial_best_accepted':False});raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--cohort',choices=('R','naming'),required=True);ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--deadline',type=float,required=True);a=ap.parse_args()
    arm(a.cohort,a.work,a.output,a.deadline)
