"""Opt-in editor bridge with typed composition; original bridge stays unchanged."""
import argparse,contextlib,hashlib,json,multiprocessing,os,secrets,signal,sys,threading,time
from http.server import ThreadingHTTPServer
from pathlib import Path
from . import editor_bridge as base,editor_task
from .records import LANE_ROOT as ROOT


def retrieve(raw,path):
    if path:
        manifest=json.loads(Path(path).read_text());adapter=manifest.get('query_adapter',{}).get('id')
        dependency=manifest.get('runtime_dependency',{}).get('id')
        if dependency is not None:
            if dependency!='algsolve.sortedcontainers-2.4.0.v1':raise ValueError('Unsupported runtime dependency')
            from .dependency_lookup import load_context,answer
            from .editor_execution import query_problem
            context,catalog=load_context(path)
            return dict(answer(context,query_problem(raw),approved_library=catalog),language='python')
        if adapter=='algsolve.named-output.v3':
            from .named_lookup import load_context,answer
            from .editor_execution import query_problem
            context,catalog=load_context(path)
            return dict(answer(context,query_problem(raw),approved_library=catalog),language='python')
        if adapter is not None:
            raise ValueError('Unsupported catalog adapter; use its declared bridge integration')
    return editor_task.retrieve(raw,approved_library=path)



def execute(language,source,problem=None,approved_library=None):
    # Inserting an approved dependency-backed answer must remain runnable. Only
    # its exact manifest-bound bytes receive that same qualified backend.
    if language=='python' and isinstance(source,str) and len(source.encode())<=65536 and problem is not None and approved_library:
        manifest=json.loads(Path(approved_library).read_text())
        profile=manifest.get('runtime_dependency',{})
        if hashlib.sha256(source.encode()).hexdigest() in profile.get('sources',{}).values():
            from .approved_library import ApprovedLibrary
            from .dependency_lookup import check_profile
            from .dependency_judge import make_judge_problem
            from .editor_execution import query_problem
            catalog=ApprovedLibrary.load(approved_library);check_profile(catalog)
            query=query_problem(problem);verdict=make_judge_problem()(query,source,query.public_tests,wall_seconds=8)
            return dict(example_passed=verdict.passed,independent_tests_passed=None,verdict=verdict.to_dict(),runtime_dependency=profile['id'])
    return editor_task.execute(language,source,problem)


def run_job(payload,connection,digest,approved_library=None):
    monitor=None
    signal.signal(signal.SIGTERM,lambda *_:sys.exit(0))
    try:
        with contextlib.redirect_stdout(sys.stderr):
            op=payload.get('operation')
            if op in ('compose','typed_check'):
                from .rebuild_recognition import Monitor
                from .embed import EMBEDDING_DIR
                monitor=Monitor([EMBEDDING_DIR,ROOT/'runs/typed-student-v2',ROOT/'runs/typed-real-dev-v5'],seconds=85);monitor.start()
                os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
                from .editor_composition import compose,check_graph
                result=compose(payload.get('problem')) if op=='compose' else check_graph(payload.get('problem'),payload.get('program'))
            elif op=='retrieve':result=retrieve(payload.get('problem'),approved_library)
            elif op=='challenge':result=editor_task.details(payload.get('slug'))
            elif op=='run':result=execute(payload.get('language'),payload.get('source'),payload.get('problem'),approved_library)
            else:raise ValueError('Unknown operation')
        result['request_binding']={'request_sha256':digest}
        if len(json.dumps(result).encode())>262144:raise ValueError('Result exceeds bridge size limit')
        connection.send({'state':'complete','result':result})
    except Exception as error:connection.send({'state':'failed','error':type(error).__name__+': '+str(error)[:500]})
    finally:
        if monitor:monitor.stop.set()
        connection.close()

class Jobs(base.Jobs):
    def start(self,payload,request_digest):
        with self.lock:
            for job in self.items.values():
                if self.poll(job)['state']=='running':raise RuntimeError('Bridge busy; wait or cancel the current job')
            self.items={key:job for key,job in self.items.items() if time.monotonic()-job['started']<120}
            if len(self.items)>=16:raise RuntimeError('Recent job limit reached')
            parent,child=self.context.Pipe(duplex=False)
            process=self.context.Process(target=run_job,args=(payload,child,request_digest,self.approved_library),daemon=True)
            process.start();child.close();job_id=secrets.token_hex(16)
            self.items[job_id]={'process':process,'pipe':parent,'started':time.monotonic()};return job_id

class Handler(base.Handler):
    def do_POST(self):
        if not self.authorized():self.send(403,{'error':'Pair this editor first'});return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if self.path!='/jobs' or not 0<length<=base.MAX_BODY or self.headers.get('Content-Type')!='application/json':raise ValueError('Invalid request size, path or content type')
            body=self.rfile.read(length);payload=json.loads(body)
            if not isinstance(payload,dict) or payload.get('operation') not in {'run','retrieve','challenge','compose','typed_check'}:raise ValueError('Unknown operation')
            self.send(202,{'id':self.server.jobs.start(payload,hashlib.sha256(body).hexdigest())})
        except RuntimeError as error:self.send(409,{'error':str(error)})
        except (ValueError,TypeError) as error:self.send(400,{'error':str(error)})

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=8875)
    parser.add_argument('--approved-library',type=Path,default=ROOT/'findings/known-sortedcontainers-1a-128-v1/approved-library.json')
    args=parser.parse_args();server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    server.token=secrets.token_urlsafe(32);server.jobs=Jobs(args.approved_library)
    signal.signal(signal.SIGTERM,lambda *_:sys.exit(0));threading.Thread(target=server.jobs.reap,daemon=True).start()
    print(f'Gamma composition bridge listening on loopback port {args.port}; explicit editor pairing required.',flush=True)
    try:server.serve_forever()
    finally:
        with server.jobs.lock:
            for job in server.jobs.items.values():server.jobs.cancel(job)
        server.server_close()
if __name__=='__main__':main()
