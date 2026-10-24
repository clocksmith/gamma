"""Phase-local52 service; no source cache, extra arm or scientific rule change."""
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import time
import common as c

SOURCE=c.LIT/'persistent-spelling-parser-v1'
spec=importlib.util.spec_from_file_location('persistent54_client52',SOURCE/'client.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
FILES=('client.py','logic.cjs','service.cjs')
LIMITS={'request_bytes':4*1024**2,'response_bytes':16*1024**2,'lexical_stdout_bytes':32*1024**2,
        'request_timeout_seconds':10,'v8_old_space_mib':256,'per_process_address_space_bytes':8*1024**3}


def implementation():return {name:c.hashfile(SOURCE/name) for name in FILES}


class Session:
    def __init__(self,phase,deadline,path,config):
        assert phase in ('fit','validation')
        assert config['parser']['implementation_sha256']==implementation()
        assert config['parser']['limits']==LIMITS
        self.phase=phase;self.deadline=deadline;self.path=Path(path)
        self.client=None;self.original=None;self.entered=False
        self.data={'schema':'gamma.persistent-spelling-parser-receipt.v1','phase':phase,'complete':False,
          'implementation_sha256':implementation(),'limits':dict(LIMITS),
          'worker_pid':os.getpid(),'worker_process_group':os.getpgrp(),'worker_core_affinity':sorted(os.sched_getaffinity(0)),
          'service_pid':None,'service_process_group':None,'service_core_affinity':None,
          'started_monotonic':None,'finished_monotonic':None,'absolute_deadline':deadline,
          'spawn_seconds':0.0,'request_seconds':0.0,'close_seconds':0.0,'lifetime_seconds':0.0,
          'requests_attempted':0,'requests_completed':0,'failed_requests':0,
          'request_bytes_total':0,'response_bytes_total':0,'max_request_bytes':0,'max_response_bytes':0,
          'service_peak_rss_kib_observed':0,'closed':False,'returncode':None,'error_type':None}

    def observe(self):
        if self.client is None:return
        try:
            lines=Path(f'/proc/{self.client.process.pid}/status').read_text().splitlines()
            peak=next(int(line.split()[1]) for line in lines if line.startswith('VmHWM:'))
            self.data['service_peak_rss_kib_observed']=max(self.data['service_peak_rss_kib_observed'],peak)
        except (FileNotFoundError,ProcessLookupError,StopIteration):pass

    def __enter__(self):
        started=time.monotonic();self.data['started_monotonic']=started
        if started>=self.deadline:raise c.HardDeadline('Absolute anchor deadline before parser startup')
        try:
            if resource.getrlimit(resource.RLIMIT_AS)[0]!=LIMITS['per_process_address_space_bytes']:
                raise RuntimeError('Parser requires inherited8GiB per-process address-space limit')
            self.client=prior.Client(timeout=min(10,self.deadline-started))
            self.data['spawn_seconds']=time.monotonic()-started
            self.data['service_pid']=self.client.process.pid
            self.data['service_process_group']=os.getpgid(self.client.process.pid)
            self.data['service_core_affinity']=sorted(os.sched_getaffinity(self.client.process.pid))
            assert self.data['service_process_group']==self.data['worker_process_group']
            assert self.data['service_core_affinity']==self.data['worker_core_affinity']
            request=self.client.request
            def counted(texts):
                begin=time.monotonic();self.data['requests_attempted']+=1
                size=len(json.dumps({'id':self.client.ident+1,'texts':texts},separators=(',',':'),ensure_ascii=True).encode())
                self.data['request_bytes_total']+=size;self.data['max_request_bytes']=max(self.data['max_request_bytes'],size)
                try:
                    remaining=self.deadline-time.monotonic()
                    if remaining<=0:raise c.HardDeadline('Absolute anchor deadline before parser request')
                    self.client.timeout=min(10,remaining)
                    bodies=request(texts)
                    # All successful source bytes are ASCII. These compact JSON
                    # envelope bytes match the52 service response, including LF.
                    response_size=len(json.dumps({'id':self.client.ident,'ok':True,'bodies':bodies},separators=(',',':'),ensure_ascii=False).encode())+1
                    self.data['response_bytes_total']+=response_size
                    self.data['max_response_bytes']=max(self.data['max_response_bytes'],response_size)
                    self.data['requests_completed']+=1
                    return bodies
                except BaseException:
                    self.data['failed_requests']+=1;raise
                finally:
                    self.data['request_seconds']+=time.monotonic()-begin;self.observe()
            self.client.request=counted
            self.original=c.p.banned;c.p.banned=self.client.banned;self.entered=True
            return self
        except BaseException as error:
            self.finish(error);raise

    def finish(self,error=None):
        if self.entered:c.p.banned=self.original;self.entered=False
        previous_handler=signal.getsignal(signal.SIGALRM)
        previous_timer=signal.getitimer(signal.ITIMER_REAL)[0]
        restored_deadline=time.monotonic()+previous_timer if previous_timer else None
        failure=error
        bound=self.deadline if failure is None else c.failure_deadline(failure,self.deadline)
        def expired(*_):
            caught=c.HardDeadline('Parser finalization deadline')
            if failure is not None:caught._gamma54_failure_deadline=bound
            else:c.failure_deadline(caught,self.deadline)
            raise caught
        def guard():
            remaining=bound-time.monotonic()
            if remaining<=0:expired()
            signal.setitimer(signal.ITIMER_REAL,remaining)
        signal.signal(signal.SIGALRM,expired)
        try:
            started=time.monotonic();guard();self.observe();guard()
            try:
                if self.client is not None:self.client.close()
            except c.HardDeadline:raise
            except BaseException as caught:
                if failure is None:failure=caught
                else:failure.add_note('Parser cleanup failed; primary failure retained')
                bound=c.failure_deadline(failure,self.deadline)
            guard()
            self.data['close_seconds']=time.monotonic()-started
            self.data['finished_monotonic']=time.monotonic()
            self.data['lifetime_seconds']=self.data['finished_monotonic']-self.data['started_monotonic']
            self.data['closed']=self.client is not None and self.client.closed
            self.data['returncode']=None if self.client is None else self.client.process.returncode
            self.data['error_type']=None if failure is None else type(failure).__name__
            self.data['complete']=failure is None and self.data['closed'] and self.data['requests_attempted']==self.data['requests_completed'] and self.data['failed_requests']==0
            guard()
            try:c.write(self.path,self.data)
            except c.HardDeadline:raise
            except BaseException as caught:
                if failure is None:
                    c.failure_deadline(caught,self.deadline);raise
                failure.add_note('Parser receipt write failed; no sealed success')
            guard()
            if error is None and failure is not None:raise failure
        finally:
            # Restore only the remaining outer timer, never its original amount.
            # Worker failure handling receives the same bound on the exception.
            signal.setitimer(signal.ITIMER_REAL,0)
            signal.signal(signal.SIGALRM,previous_handler)
            if restored_deadline is not None:
                remaining=restored_deadline-time.monotonic()
                if remaining>0:signal.setitimer(signal.ITIMER_REAL,remaining)

    def __exit__(self,kind,error,tb):self.finish(error)
