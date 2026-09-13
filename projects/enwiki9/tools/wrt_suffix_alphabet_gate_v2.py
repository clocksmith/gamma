#!/usr/bin/env python3
"""Exact bounded strong-codec comparison of a fixed dictionary alphabet."""
from pathlib import Path
import hashlib, json, os, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[1]
CID='wrt_suffix_alphabet250k_q0_v2'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out=ROOT/'results'/CID
    e=json.loads((ROOT/'operations/adaptive/experiments'/(CID+'.json')).read_text())
    for r in e['inputs']:assert digest(ROOT/r['path'])==r['sha256'].removeprefix('sha256:')
    snap=Path(os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT'])
    sys.path.insert(0,str(snap));from program import transform
    assert (snap/'program.py').read_bytes()==(ROOT/'tools/wrt_suffix_alphabet_v1.py').read_bytes()
    base=ROOT/'operations/evidence/wrt_suffix_alphabet_v1'
    raw=ROOT/'operations/evidence/fixtures/dualstream_opening250k_v1.raw'
    dictionary=(base/'english.dic').read_bytes();binary=base/'cmix.bin'
    env=os.environ.copy();env.update(CMIX_PRETRAIN_FILE=str(base/'english.dic'),CMIX_MMAP_ALLOC='0',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',TMPDIR=str(out))
    marker=Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS']);phases=[];arms={}
    for arm in 'PKDS':
        dic=out/(arm+'.dic');dic.write_bytes(transform(dictionary,arm))
        for action,flag,src,dst in [('encode','-t',raw,out/(arm+'.arc')),('decode','-d',out/(arm+'.arc'),out/(arm+'.raw')),('repeat','-t',raw,out/(arm+'.repeat.arc'))]:
            phase=arm+'-'+action
            with marker.open('a') as f:f.write(json.dumps(dict(phase=phase,event='start'))+'\n')
            command=[str(binary),flag,str(dic),str(src),str(dst)]
            started=time.monotonic()
            with (out/(phase+'.stdout')).open('wb') as stdout,(out/(phase+'.stderr')).open('wb') as stderr:
                p=subprocess.run(command,cwd=out,env=env,stdout=stdout,stderr=stderr,timeout=270)
            r=dict(phase=phase,command=command,returncode=p.returncode,elapsed_seconds=time.monotonic()-started)
            (out/(phase+'.execution.json')).write_text(json.dumps(r,indent=2)+'\n');phases.append(r)
            assert p.returncode==0,phase
            if action=='decode':assert dst.read_bytes()==raw.read_bytes(),phase
            if action=='repeat':assert dst.read_bytes()==(out/(arm+'.arc')).read_bytes(),phase
            if arm=='P' and action=='encode':
                assert dst.stat().st_size==44958 and digest(dst)=='8159fad519e0d409dbda296b3f6bbe348a541e59a090a5001b18b8bfe655ca0d','retained-parent parity'
            with marker.open('a') as f:f.write(json.dumps(dict(phase=phase,event='end'))+'\n')
        arms[arm]=dict(archive_bytes=(out/(arm+'.arc')).stat().st_size,archive_sha256=digest(out/(arm+'.arc')),dictionary_sha256=digest(dic),roundtrip=True,repeat=True)
        if arm=='K':assert (out/'P.arc').read_bytes()==(out/'K.arc').read_bytes() and (out/'P.dic').read_bytes()==dic.read_bytes()
    gP=arms['P']['archive_bytes']-arms['D']['archive_bytes'];gS=arms['S']['archive_bytes']-arms['D']['archive_bytes']
    result=dict(schema='gamma.enwiki9.wrt-suffix-alphabet-comparison.v1',candidate_id=CID,raw_population='[0, 250000)',input_bytes=raw.stat().st_size,input_sha256=digest(raw),arms=arms,g_P=gP,g_S=gS,source_bytes=(snap/'program.py').stat().st_size,retained_parent_archive_parity=True,PK_archive_byte_identity=True,all_exact_inverses=True,all_archive_repeats=True,internal_state_witness=None,internal_state_note='Black-box exact archive/inverse/repeat comparison with the identical retained native executable. Internal predictive states are not instrumented; no state-trace confirmation is claimed.',complete_package_bytes=None,full_corpus_score_bytes=None,objective_credit_bytes=0,verdict=('archive regression on this sample' if gP<0 else 'no archive improvement on this sample' if gP==0 else 'parent archive improvement; shuffled-control advantage unconfirmed' if gS<=0 else 'archive improvement against parent and shuffled control on this exposed sample'),phases=phases)
    (out/'decision.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['g_P','g_S','verdict']}))
if __name__=='__main__':main()
