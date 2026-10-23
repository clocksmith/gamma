"""Frozen execution only; launch.py supplies a separate process-group guard."""
import argparse
import concurrent.futures
import json
import multiprocessing
import os
from pathlib import Path
import platform
import signal
import sys
import time
from common import HERE,LIT,analyze,authority,checked,evaluate,sha,write,enforce_limits
# Prefer this directory after legacy backend imports adjust sys.path.
sys.path.insert(0,str(HERE))
from engine import fit_arm

def main(out):
    started=time.monotonic();out.mkdir(parents=True,exist_ok=False);phase='preflight';pool=None
    def timeout(*_):raise TimeoutError('global execution deadline')
    c=json.loads((HERE/'contract.json').read_text())
    signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,c['overall_seconds'])
    try:
        enforce_limits(c)
        write(out/'status.json',{'phase':phase,'complete':False})
        import numpy,scipy
        assert Path(sys.executable).absolute()==Path(c['python_bin']).absolute()
        assert c['versions']=={'python':platform.python_version(),'numpy':numpy.__version__,'scipy':scipy.__version__}
        assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
        for rel,h in c['code_hashes'].items():assert sha((LIT/rel).read_bytes())==h,rel
        for path,h in c['runtime_files'].items():assert sha(Path(path).read_bytes())==h,path
        # Deliberately do not hash/read combined sources or baseline inputs here.
        phase='fit';write(out/'status.json',{'phase':phase,'complete':False})
        pool=concurrent.futures.ProcessPoolExecutor(max_workers=4,mp_context=multiprocessing.get_context('spawn'))
        jobs=[(w,m,str(out),c,core) for (w,m),core in zip(((7,'fixed96'),(7,'optional'),(8,'fixed96'),(8,'optional')),c['cores'])]
        summaries=list(pool.map(fit_arm,jobs));pool.shutdown();pool=None
        write(out/'all-fit-sealed.json',{'validation_loaded':False,'summaries':summaries})
        phase='validation';write(out/'status.json',{'phase':phase,'complete':False});arms=[]
        for w in (7,8):
            inp=c['inputs'][str(w)];sources=checked(inp['sources']);original=checked(inp['original_sources'])
            expected=set(map(str,c['partition']['dev_fit']+c['partition']['dev_val']))
            assert set(sources)==set(original)==expected
            authority(c,w,'scope_joint',sources);authority(c,w,'control',original)
            for name,texts,vocab in [('R',original,checked(inp['baseline_dictionary'])),('seed31',sources,checked(inp['seed_dictionary']))]+[(m,sources,json.loads((out/f'w{w}'/m/'dictionary.json').read_text())) for m in ('fixed96','optional')]:
                folder=out/f'w{w}'/name;folder.mkdir(parents=True,exist_ok=True)
                write(folder/'sources.json',texts);write(folder/'dictionary.json',vocab)
                a=evaluate(texts,vocab,w,c);a['arm']=name
                a['dictionary_sha256']=sha((folder/'dictionary.json').read_bytes())
                a['sources_sha256']=sha((folder/'sources.json').read_bytes())
                a['qualification_receipt_sha256']=c['qualification']['sha256']
                (folder/'packets').mkdir();db=analyze.dictionary_bytes(vocab);(folder/'dictionary.bin').write_bytes(db)
                for pid,row in a['per_problem'].items():
                    if row['encodable']:(folder/'packets'/f'{pid}.bin').write_bytes(analyze.encode(vocab,analyze.shortest_encode(texts[pid],vocab),w))
                if name in ('fixed96','optional'):
                    summary=next(s for s in summaries if s['width']==w and s['arm']==name)
                    assert a['fit']['covered']==27 and a['fit']['selections']['total']==summary['fit_selections']
                arms.append(a)
        write(out/'results.json',{'contract_sha256':sha((HERE/'contract.json').read_bytes()),'arms':arms,'seconds':time.monotonic()-started})
        write(out/'status.json',{'phase':'complete','complete':True})
    except BaseException as e:
        write(out/'failure.json',{'phase':phase,'error_type':type(e).__name__,'error':str(e),'complete':False,'promotion_allowed':False,'seconds':time.monotonic()-started})
        write(out/'status.json',{'phase':phase,'complete':False});raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        if pool is not None:pool.kill_workers()

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);main(ap.parse_args().output)
