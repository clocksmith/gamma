"""Bounded synthetic-only timing experiment; no private input arguments exist."""
import argparse,hashlib,json,os,resource,signal,sys,time
from pathlib import Path
import mechanism as m
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def fixture():
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_+-*/(){};,'
    lengths=[100+(137*i)%301 for i in range(300)];lengths[-1]+=75000-sum(lengths)
    texts={str(p):''.join(alphabet[(i*17+p*7+(i//13)*3)%len(alphabet)] for i in range(n)) for p,n in enumerate(lengths)}
    q={p:[[((int(p)*29+i*13+b*7)%101) for b in range(11)] for i in range(len(t))] for p,t in texts.items()}
    banned=set(texts.values())|{t[3:-3] for t in texts.values()};ends={p:[set() for _ in t] for p,t in texts.items()}
    for p,text in texts.items():
        for word in banned:
            at=text.find(word)
            while at>=0:ends[p][at].add(at+len(word));at=text.find(word,at+1)
    digest=lambda obj:sha(json.dumps(obj,sort_keys=True,separators=(',',':')).encode())
    manifest={'programs':len(texts),'characters':sum(lengths),'minimum_length':min(lengths),'maximum_length':max(lengths),
              'sources_sha256':digest(texts),'q_sha256':digest(q),'exact_bans_sha256':digest(sorted(banned)),
              'banned_occurrences':sum(len(row) for rows in ends.values() for row in rows)}
    assert manifest['characters']==75000 and min(lengths)>0
    return texts,q,ends,manifest

def spec():
    _,_,_,manifest=fixture()
    return {'synthetic_only':True,'fixture':manifest,'denominator':1000,'penalties':[0,250,500,1000,2000,4000,8000,16000],
        'maximum_cardinality':96,'cores':{'penalty':4,'exact':5},'outer_seconds':120,'worker_seconds':115,'address_space_bytes':8*1024**3,
        'python_bin':str(Path(sys.executable).resolve()),'python_sha256':sha(Path(sys.executable).resolve().read_bytes()),
        'code_hashes':{n:sha((HERE/n).read_bytes()) for n in ('mechanism.py','test_mechanism.py','benchmark.py')},
        'parent_contract_sha256':sha((LIT/'length-sensitive-fraction-v1/contract.json').read_bytes())}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--make-spec',action='store_true');ap.add_argument('--mode',choices=('penalty','exact'));args=ap.parse_args()
    if args.make_spec:
        (HERE/'synthetic-contract.json').write_text(json.dumps(spec(),sort_keys=True,indent=2)+'\n');print('Synthetic specification written; no path benchmark run.');return
    assert args.mode is not None;c=json.loads((HERE/'synthetic-contract.json').read_text());assert c==spec()
    os.sched_setaffinity(0,{c['cores'][args.mode]});resource.setrlimit(resource.RLIMIT_AS,(c['address_space_bytes'],)*2)
    started=time.monotonic();receipt={'mode':args.mode,'synthetic_only':True,'complete':False,'contract_sha256':sha((HERE/'synthetic-contract.json').read_bytes()),'stages':{}}
    path=HERE/f'synthetic-{args.mode}.json';phase='preflight'
    def save():path.write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    def timeout(signum,frame):raise TimeoutError('synthetic worker cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(c['worker_seconds'])
    try:
        prior=json.loads((LIT/'length-sensitive-fraction-v1/contract.json').read_text())
        for rel,h in prior['code_hashes'].items():assert sha((LIT/rel).read_bytes())==h
        texts,q,ends,manifest=fixture();assert manifest==c['fixture'];receipt['fixture']=manifest
        phase='paths';clock=time.monotonic()
        if args.mode=='penalty':
            caps,unrestricted=m.penalty_caps(texts,q,c['denominator'],ends,c['penalties'])
        else:
            caps=m.exact_caps(texts,q,c['denominator'],ends,c['maximum_cardinality'])
            unrestricted=m.parent.heap_paths(texts,q,c['denominator'],ends)
        receipt['stages']['paths_seconds']=time.monotonic()-clock;save();print(json.dumps(receipt),flush=True)
        phase='necessary_assignment';clock=time.monotonic()
        rows=[[caps[p][32],caps[p][96],unrestricted[p]] for p in sorted(texts)]
        value=m.three_class_assignment(rows,150,135,15)
        receipt['stages']['necessary_assignment_seconds']=time.monotonic()-clock
        receipt['necessary_assignment_path_numerator']=value;receipt['unrestricted_path_numerator']=sum(unrestricted.values());save()
        assert value is None or value>=sum(unrestricted.values())
        if args.mode=='exact':
            phase='exact_median_assignment';clock=time.monotonic()
            joint,union=m.exact_median_assignment(caps,unrestricted)
            receipt['stages']['exact_median_assignment_seconds']=time.monotonic()-clock
            receipt['exact_median_path_numerator']=joint;receipt['feasible_median_cases']=sum(v is not None for v in union)
            assert joint is None or joint>=value
        receipt.update(complete=True,elapsed=time.monotonic()-started,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    except BaseException as error:
        receipt.update(failure_type=type(error).__name__,failed_phase=phase,elapsed=time.monotonic()-started,
                       peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        raise
    finally:signal.alarm(0);save();print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
