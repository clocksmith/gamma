"""Fixed fit-only repair pairs: identical model, with or without the known incumbent."""
import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import platform
import random
import sys
import time
import numpy as np
import scipy
import model as m
HERE=m.HERE;LIT=m.LIT;analyze=m.analyze

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x);return x
sys.path.insert(0,str(LIT/'character-slots-v1'))
slots=module('seeded_slots_driver',LIT/'character-slots-v1/run.py')


def pair(job):
    no,out,work,c=job;out=Path(out);work=Path(work);os.sched_setaffinity(0,{12+no%4});folder=out/f'trial-{no:02d}'
    snapshot=json.loads((folder/'snapshot.json').read_text());texts=json.loads((work/c['seed_relative_path']/'fit-sources.json').read_text());seed=json.loads((work/c['seed_relative_path']/'dictionary.json').read_text())
    fixed,candidates,capacity=snapshot['fixed'],snapshot['candidates'],snapshot['capacity']
    model=m.build(texts,fixed,candidates,capacity,seed);matrix=model['matrix'];h=hashlib.sha256()
    for array in (matrix.indptr,matrix.indices,matrix.data,model['lower'],model['upper'],model['cost'],model['start']):h.update(array.tobytes())
    modelhash=h.hexdigest();runs=[];banned=slots.sel.forbidden_strings(texts)
    order=[False,True] if no%2==0 else [True,False]
    for warm in order:
        name='warm' if warm else 'cold';root=folder/name;root.mkdir();chosen,info=m.solve(model,candidates,warm,c['solver_seconds'],c['solver_seed'])
        info.update(trial=no,mode=snapshot['mode'],order=len(runs),model_sha256=modelhash,validation_loaded=False)
        analyze.write(root/'solver.json',info)
        vocab=slots.ordered(fixed+chosen) if info['feasible'] else None;rows={};score=None;dictbytes=None
        if vocab is not None:
            assert len(vocab)==len(set(vocab))<=256 and not set(vocab)&banned
            score,_,_=m.slot.exact(texts,vocab);assert score<=info['objective']+1e-6
            if info['optimal']:assert abs(score-info['objective'])<=1e-6
            analyze.write(root/'dictionary.json',vocab);db=analyze.dictionary_bytes(vocab);(root/'dictionary.bin').write_bytes(db);(root/'packets').mkdir();dictbytes=len(db)
            for pid,text in texts.items():
                seq=analyze.shortest_encode(text,vocab);packet=analyze.encode(vocab,seq,8);assert analyze.decode(db,packet)==text
                rows[pid]={'source_sha256':analyze.sha(text.encode()),'selections':len(seq),'actions':len(seq)+1,'characters':sum(len(vocab[k])==1 for k in seq),
                           'packet_bytes':len(packet),'packet_sha256':analyze.sha(packet),'one_program_package_bytes':len(db)+len(packet)}
                (root/'packets'/f'{pid}.bin').write_bytes(packet)
            info.update(dictionary_sha256=analyze.sha((root/'dictionary.json').read_bytes()),entries=len(vocab),character_entries=sum(len(s)==1 for s in vocab))
        info.update(exact=score,improves=score is not None and score<model['initial'],nonworse=score is not None and score<=model['initial'],
                    per_problem=rows,decoded=len(rows),dictionary_bytes=dictbytes,initial=model['initial'],
                    package_bytes=dictbytes+sum(x['packet_bytes'] for x in rows.values()) if vocab is not None else None)
        runs.append(info);analyze.write(root/'results.json',info)
        print(json.dumps({k:v for k,v in info.items() if k!='per_problem'}),flush=True)
    result={'trial':no,'mode':snapshot['mode'],'snapshot_sha256':analyze.sha((folder/'snapshot.json').read_bytes()),'model_sha256':modelhash,
            'start_checked':True,'initial':model['initial'],'build_seconds':model['build_seconds'],'arcs':model['arcs'],'variables':model['variables'],
            'candidate_count':len(candidates),'capacity':capacity,'freed':snapshot['freed'],'runs':runs}
    analyze.write(folder/'results.json',result);return result


def main(work,out):
    c=json.loads((HERE/'contract.json').read_text());assert str(Path(sys.executable).absolute())==c['python_bin']
    assert c['versions']=={'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}
    assert os.environ.get('OMP_NUM_THREADS')==os.environ.get('OPENBLAS_NUM_THREADS')=='1'
    for rel,h in c['code_hashes'].items():assert analyze.sha((LIT/rel).read_bytes())==h,rel
    for path,h in c['runtime_files'].items():assert analyze.sha(Path(path).read_bytes())==h,path
    for rel,h in c['private_files'].items():assert analyze.sha((work/rel).read_bytes())==h,rel
    out.mkdir(parents=True,exist_ok=False);started=time.monotonic();seedroot=work/c['seed_relative_path']
    texts=json.loads((seedroot/'fit-sources.json').read_text());seed=json.loads((seedroot/'dictionary.json').read_text());assert set(texts)=={str(i) for i in c['fit_ids']}
    proof=json.loads((LIT/'lns-naming-v1/evidence/results.json').read_text());proof=next(a for a in proof['arms'] if a['arm']=='seed_fixed_seed')
    for pid,text in texts.items():assert analyze.sha(text.encode())==proof['per_problem'][pid]['source_sha256'] and proof['qualification'][pid]['passed']
    initial,_,usage=m.slot.exact(texts,seed);observed=set(''.join(texts.values()));reserved=set(m.slot.ALPHABET)-observed;banned=slots.sel.forbidden_strings(texts)
    pool,ranked=slots.pool_rank(texts,banned,c['proposal']['max_length']);analyze.write(out/'pool.json',pool)
    snapshots=[]
    for no in range(8):
        mode='fixed96' if no<4 else 'optional';fixed,candidates,capacity,freed=m.slot.proposal(seed,observed,reserved,pool,ranked,random.Random(260+no),mode,c['proposal'],usage)
        folder=out/f'trial-{no:02d}';folder.mkdir();analyze.write(folder/'snapshot.json',{'trial':no,'mode':mode,'fixed':fixed,'candidates':candidates,'capacity':capacity,'freed':freed})
        snapshots.append(analyze.sha((folder/'snapshot.json').read_bytes()))
    analyze.write(out/'all-snapshots-sealed.json',{'before_solver_calls':True,'validation_loaded':False,'snapshot_hashes':snapshots})
    jobs=[(no,str(out.resolve()),str(work.resolve()),c) for no in range(8)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=4,mp_context=multiprocessing.get_context('spawn')) as executor:results=list(executor.map(pair,jobs))
    analyze.write(out/'results.json',{'pairs':results,'seconds':time.monotonic()-started,'contract_sha256':analyze.sha((HERE/'contract.json').read_bytes()),
                'validation_loaded':False,'pool_sha256':analyze.sha((out/'pool.json').read_bytes()),'initial':initial})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();main(a.work,a.output)
