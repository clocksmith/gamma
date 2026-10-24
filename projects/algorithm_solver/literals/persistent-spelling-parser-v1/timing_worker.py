"""One fresh invented timing block; invoked only by the bounded supervisor."""
import time
STARTED = time.monotonic()
import argparse
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import sys
import client
import fixtures
import pin_timing as pin


class Deadline(BaseException): pass


def load46():
    old=sys.modules.get('common');paths=list(sys.path)
    try:
        spec=importlib.util.spec_from_file_location('timing52_common46',pin.LIT/'postfit-spelling-stack-v1/common.py')
        c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);sys.modules['common']=c
        spec=importlib.util.spec_from_file_location('timing52_engine46',pin.LIT/'postfit-spelling-stack-v1/engine.py')
        e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e);return c,e
    finally:
        sys.path[:]=paths
        if old is None:sys.modules.pop('common',None)
        else:sys.modules['common']=old


def write(path,value):
    temp=path.with_suffix('.pending');temp.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');temp.replace(path)


def main(block,output,deadline):
    pin.require_checks();assert block in fixtures.BLOCKS
    resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,)*2);os.sched_setaffinity(0,{4})
    def expired(*_):raise Deadline('Whole benchmark deadline')
    signal.signal(signal.SIGALRM,expired)
    remaining=deadline-time.monotonic()
    if remaining<=0:raise Deadline('Expired before imports')
    signal.setitimer(signal.ITIMER_REAL,remaining)
    service=None;c=None;old=None;result=None;failure=None
    try:
        c,e=load46();old=c.p.banned
        startup=time.monotonic()
        if block.startswith('persistent'):
            service=client.Client(timeout=min(10,deadline-time.monotonic()))
            write(output/(block+'-service.json'),{'pid':service.process.pid})
            def bounded(texts):
                service.timeout=min(10,deadline-time.monotonic())
                if service.timeout<=0:raise Deadline('Whole benchmark deadline')
                return service.banned(texts)
            c.p.banned=bounded
        startup_seconds=time.monotonic()-startup
        scalar_start=time.monotonic();answers=[]
        for request in fixtures.scalar_requests(): answers.append(sorted(c.p.banned(request)))
        scalar_seconds=time.monotonic()-scalar_start
        texts,vocab=fixtures.engine_inputs();menu_start=time.monotonic();menu=e.menu(texts,vocab)
        menu_seconds=time.monotonic()-menu_start;apply_start=time.monotonic()
        applied=e.apply(texts,vocab,menu,proposal_cap=153600)
        apply_seconds=time.monotonic()-apply_start
        assert applied['complete'] is True
        untimed=dict(applied);untimed.pop('seconds')
        semantics={'scalar_sha256':fixtures.digest(answers),'scalar_requests':len(answers),
          'scalar_total_bans':sum(map(len,answers)),'menu_sha256':fixtures.digest(menu),
          'engine_result_sha256':fixtures.digest(untimed),'trace_sha256':fixtures.digest(applied['trace']),
          'ledger_sha256':fixtures.digest(applied['ledger']),'selected_sha256':fixtures.digest(applied['selected']),
          'sources':len(texts),'names':len(menu['names']),'contexts':len(menu['contexts']),
          'proposals':applied['proposals'],'accepted':applied['accepted'],
          'variants':len(applied['ledger']['variants']),'encounters':len(applied['ledger']['encounters'])}
        result={'complete':True,'block':block,'semantics':semantics,
          'timing':{'service_spawn_seconds':startup_seconds,'scalar_seconds':scalar_seconds,
                    'menu_seconds':menu_seconds,'apply_seconds':apply_seconds}}
    except BaseException as error:failure=error
    finally:
        cleanup_start=time.monotonic()
        if c is not None and old is not None:c.p.banned=old
        try:
            if service is not None:service.close()
        except BaseException as error:
            if failure is None:failure=error
        cleanup=time.monotonic()-cleanup_start
    try:
        if failure is not None:raise failure
        if time.monotonic()>=deadline:raise Deadline('Whole benchmark deadline')
        result['timing'].update(cleanup_seconds=cleanup,worker_seconds=time.monotonic()-STARTED)
        result['self_peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result['children_max_rss_kib']=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        write(output/(block+'.json'),result)
        if time.monotonic()>=deadline:raise Deadline('Whole benchmark deadline')
    except BaseException as error:
        try:
            (output/(block+'.json')).unlink(missing_ok=True)
            write(output/(block+'.json'),{'complete':False,'block':block,'error_type':type(error).__name__})
        finally:raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--block',choices=fixtures.BLOCKS,required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--deadline',type=float,required=True)
    a=ap.parse_args();main(a.block,a.output,a.deadline)
