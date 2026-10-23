"""Fit-only capacity certificates and feasible witnesses; never reads validation."""
import argparse
import concurrent.futures
import json
import multiprocessing
import os
from pathlib import Path
import platform
import sys
import time
import resource
import numpy as np
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'fraction-capacity-v1'))
import dual as d
analyze=d.analyze
sys.path.insert(0,str(HERE))
import pool as shared_pool
import occurrence
d.Graph=occurrence.Graph
d.independent_certificate=occurrence.independent_certificate


def measure(texts,vocab,folder,decoder_bytes):
    folder.mkdir();analyze.write(folder/'dictionary.json',vocab);db=analyze.dictionary_bytes(vocab);(folder/'dictionary.bin').write_bytes(db);(folder/'packets').mkdir();rows={}
    for pid,text in sorted(texts.items()):
        value,seq=d.encode_objective(text,vocab);packet=analyze.encode(vocab,seq,8)
        assert analyze.decode(db,packet)==text
        row={'source_sha256':analyze.sha(text.encode()),'selections':len(seq),'actions':len(seq)+1,'characters':sum(len(vocab[i])==1 for i in seq),
             'objective':value,'packet_bytes':len(packet),'packet_sha256':analyze.sha(packet),'one_program_package_bytes':len(db)+len(packet),
             'one_program_with_decoder':len(db)+len(packet)+decoder_bytes}
        assert value==10*row['characters']-len(seq);rows[pid]=row;(folder/'packets'/f'{pid}.bin').write_bytes(packet)
    n=sum(x['selections'] for x in rows.values());chars=sum(x['characters'] for x in rows.values());package=len(db)+sum(x['packet_bytes'] for x in rows.values())
    return {'per_problem':rows,'selections':analyze.distribution([x['selections'] for x in rows.values()]),'actions':analyze.distribution([x['actions'] for x in rows.values()]),
            'characters':chars,'character_fraction':chars/n,'objective':10*chars-n,'entries':len(vocab),'character_entries':sum(len(s)==1 for s in vocab),
            'dictionary_sha256':analyze.sha((folder/'dictionary.json').read_bytes()),'dictionary_bytes':len(db),'package_bytes':package,
            'package_with_decoder_sources':package+decoder_bytes,'amortized_package_bytes':package/len(rows),'framing_bytes':41*len(rows),'payload_bits':8*n,'padding_bits':0}


def arm(job):
    cohort,cores,work,out,c=job;mode='flex256';os.sched_setaffinity(0,set(cores))
    resource.setrlimit(resource.RLIMIT_AS,(c['limits']['address_space_bytes'],c['limits']['address_space_bytes']))
    work=Path(work);out=Path(out);started=time.monotonic()
    seedroot=work/c['cohorts'][cohort];texts=json.loads((seedroot/'fit-sources.json').read_text());seed=json.loads((seedroot/'dictionary.json').read_text())
    assert set(texts)=={str(i) for i in c['fit_ids']} and set(''.join(texts.values()))<=set(d.ALPHABET)
    banned=d.sel.forbidden_strings(texts);assert not set(seed)&banned
    pool_started=time.monotonic();shared=shared_pool.build_pool(texts,banned)
    assert len(shared)==len(set(shared)) and shared==sorted(shared)
    extras=sorted({s for s in seed if len(s)>1}-set(shared))
    pool=sorted(set(shared)|set(extras));pool_seconds=time.monotonic()-pool_started
    assert not set(pool)&banned
    mandatory=[];pool=sorted(set(pool)|set(d.ALPHABET));capacity=256
    folder=out/f'{cohort}-{mode}';folder.mkdir();analyze.write(folder/'pool.json',pool)
    def trace(row):
        row.update(validation_loaded=False)
        with (folder/'trace.jsonl').open('a') as f:f.write(json.dumps(row,sort_keys=True)+'\n')
        if row['iteration']%100==0:print(json.dumps({'arm':folder.name,**row}),flush=True)
    graph,info,q,best,generated=d.optimize(texts,pool,mandatory,capacity,seed,c['search'],trace)
    numerator=d.independent_certificate(texts,pool,mandatory,q,capacity,c['search']['denominator']);assert numerator==info['certificate']['numerator']
    np.save(folder/'certificate-q.npy',np.asarray(q,dtype=np.int64))
    info['certificate'].update(q_sha256=analyze.sha((folder/'certificate-q.npy').read_bytes()),independent_forward_verified=True,
        excludes_ten_percent=info['certificate']['integer_lower_bound']>0)
    witnesses={}
    for name,vocab in [('seed',seed),('best',best),('generated',generated)]:
        if vocab is None:continue
        assert len(vocab)<=256 and set(mandatory)<=set(vocab) and len(set(vocab)-set(mandatory))<=capacity and not set(vocab)&banned
        witnesses[name]=measure(texts,vocab,folder/name,c['decoder_dependency_bytes'])
        assert info['certificate']['integer_lower_bound']<=witnesses[name]['objective']
    assert witnesses['best']['objective']==info['best_objective']
    result={'cohort':cohort,'mode':mode,'fit_problems':len(texts),'validation_loaded':False,'pool_entries':len(pool),'occurrences':len(graph.occ_entry),
            'capacity':capacity,'mandatory_entries':len(mandatory),
            'shared_learned_entries':len(shared),'seed_extra_entries':len(extras),'seed_extras_sha256':analyze.sha(json.dumps(extras,ensure_ascii=True).encode()),
            'maximum_entry_length':max(map(len,pool),default=0),'pool_seconds':pool_seconds,
            'pool_scope':'Every length>=2 substring shared by at least two distinct fit programs, excluding fit source/body bans; union all pinned seed learned extras and 96 characters.',
            'pool_sha256':analyze.sha((folder/'pool.json').read_bytes()),
            'fit_source_sha256':c['private_files'][c['cohorts'][cohort]+'/fit-sources.json'],'optimization':info,'witnesses':witnesses,
            'source_qualification':'exact hash reuse from item13; no source execution','seconds':time.monotonic()-started}
    analyze.write(folder/'results.json',result);print(json.dumps({'complete':folder.name,'bound':info['certificate']['integer_lower_bound'],'upper':info['best_objective'],'seconds':result['seconds']}),flush=True);return result


def main(work,out):
    started=time.monotonic();c=json.loads((HERE/'contract.json').read_text());assert str(Path(sys.executable).absolute())==c['python_bin']
    assert {'python':platform.python_version(),'numpy':np.__version__}==c['versions']
    assert os.environ.get('OMP_NUM_THREADS')==os.environ.get('OPENBLAS_NUM_THREADS')=='1'
    for rel,h in c['code_hashes'].items():assert analyze.sha((LIT/rel).read_bytes())==h,rel
    for path,h in c['runtime_files'].items():assert analyze.sha(Path(path).read_bytes())==h,path
    for rel,h in c['private_files'].items():assert analyze.sha((work/rel).read_bytes())==h,rel
    # Qualification identity checks are fit-only; no source/case payload from validation is read.
    proof=json.loads((LIT/'binding-descent-v1/evidence/results.json').read_text())
    for cohort,seedrel in c['cohorts'].items():
        a=next(a for a in proof['arms'] if a['arm']==('control' if cohort=='R' else 'scope_joint') and a['width']==8)
        texts=json.loads((work/seedrel/'fit-sources.json').read_text())
        for pid,text in texts.items():assert analyze.sha(text.encode())==a['per_problem'][pid]['source_sha256'] and a['qualification'][pid]['passed']
    out.mkdir(parents=True,exist_ok=False);jobs=[]
    for cohort in ('R','naming'):jobs.append((cohort,c['limits']['arm_cores'][cohort],str(work.resolve()),str(out.resolve()),c))
    with concurrent.futures.ProcessPoolExecutor(max_workers=2,mp_context=multiprocessing.get_context('spawn')) as executor:
        futures=[executor.submit(arm,job) for job in jobs]
        try:
            results=[f.result(timeout=max(0.,c['limits']['overall_seconds']-(time.monotonic()-started))) for f in futures]
        except BaseException as error:
            # Python3.14 kills worker processes; no clipped pool or partial certificate is accepted.
            executor.kill_workers()
            analyze.write(out/'failure.json',{'exception':type(error).__name__,'seconds':time.monotonic()-started,
                'complete':False,'partial_certificates_promoted':False,'validation_loaded':False})
            raise
    analyze.write(out/'results.json',{'arms':results,'seconds':time.monotonic()-started,'contract_sha256':analyze.sha((HERE/'contract.json').read_bytes()),'validation_loaded':False})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();main(a.work,a.output)
