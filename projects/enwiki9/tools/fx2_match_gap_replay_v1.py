#!/usr/bin/env python3
"""Validate bound observations, exact opportunity ceiling and finite replay."""
import hashlib,json,struct,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lib.fx2_match_gap_v1 import Controller,perfect_bound
from tools.causal_field_parent_coder_v1 import Encoder,Decoder
from tools.wrt_exact import parse_store_bytes,read_dictionary_words

def digest(b):return hashlib.sha256(b).hexdigest()

def run(trace,stored,raw,dictionary,parent,coder,out):
    out.mkdir()
    body=stored[10:];words=read_dictionary_words(dictionary)
    if parse_store_bytes(stored,words).decoded!=raw:raise ValueError('WRT input differs')
    if len(trace)!=len(body)*64 or len(coder)!=len(body)*224:raise ValueError('population length differs')
    records=list(struct.iter_unpack('<HBBBBH',trace));hist=Counter();active_bytes=0;agreement=[0,0];previous=None
    for i,((c,f,y,d,s,r),p) in enumerate(zip(records,struct.iter_unpack('<7I',coder))):
        if f&~15 or f&7!=i%8 or (c,y)!=(p[1],p[6]) or y!=(body[i//8]>>(7-i%8))&1:raise ValueError('count,clock or truth differs')
        if bool(f&8)!=(64<=r<=255) or (not r and (d or s)):raise ValueError('eligibility differs')
        if i%8 and (f&8,d,s,r)!=previous:raise ValueError('within-byte donor changed')
        previous=(f&8,d,s,r)
        if f&8:
            hist[c if y else 65536-c]+=1
            if i%8==0:
                active_bytes+=1;agreement[0]+=d==body[i//8];agreement[1]+=s==body[i//8]
    bound=perfect_bound(hist);results=[]
    for arm in 'PDS':
        ctl=None if arm=='P' else Controller(arm=='S')
        enc=Encoder(max_bits=len(body)*8,max_payload_bytes=len(body)*2);witness=hashlib.sha256();probs=hashlib.sha256();changed=0
        for c,f,y,d,s,r in records:
            q=c if ctl is None else ctl.predict(c,f,d,s);enc.encode(y,q);probs.update(struct.pack('<H',q));changed+=q!=c
            if ctl:
                ctl.observe(y)
                if ctl.clock%8==0:witness.update(ctl.state())
        payload=enc.finish();archive=parent[:46]+payload
        if arm=='P' and archive!=parent:raise ValueError('native parent replay differs')
        (out/(arm+'.arc')).write_bytes(archive)
        dec=Decoder(payload,max_bits=len(body)*8,max_payload_bytes=len(body)*2,expected_payload_bytes=len(payload),payload_sha256=digest(payload))
        re=Encoder(max_bits=len(body)*8,max_payload_bytes=len(body)*2);ct=None if arm=='P' else Controller(arm=='S');restored=bytearray(len(body));dw=hashlib.sha256();dp=hashlib.sha256()
        for i,(c,f,_ignored_truth,d,s,r) in enumerate(records):
            q=c if ct is None else ct.predict(c,f,d,s);y=dec.decode(q);re.encode(y,q);dp.update(struct.pack('<H',q))
            if (re.low,re.high)!=(dec.low,dec.high):raise ValueError('independent intervals differ')
            restored[i//8]=(restored[i//8]<<1)|y
            if ct:
                ct.observe(y)
                if ct.clock%8==0:dw.update(ct.state())
        if restored!=body or re.finish()!=payload or dp.digest()!=probs.digest() or dw.digest()!=witness.digest():raise ValueError('conditional inverse/state/repeat differs')
        decoded=parse_store_bytes(stored[:10]+restored,words).decoded
        if decoded!=raw:raise ValueError('raw inverse differs')
        (out/(arm+'.raw')).write_bytes(decoded)
        results.append(dict(arm=arm,archive_bytes=len(archive),archive_sha256=digest(archive),changed_probability_events=changed,probability_sha256=probs.hexdigest(),state_sha256=witness.hexdigest(),exact_conditional_inverse=True))
    sizes={r['arm']:r['archive_bytes'] for r in results};g=sizes['P']-sizes['D'];s=sizes['S']-sizes['D']
    o=dict(schema='gamma.enwiki9.match-gap-replay.v1',modeled_bytes=len(body),active_bytes=active_bytes,active_events=sum(hist.values()),aligned_exact_bytes=agreement[0],shifted_exact_bytes=agreement[1],perfect_ideal_upper_bits_ceil=bound,perfect_ideal_upper_bytes_ceil=(bound+7)//8,bound_scope='Only fixed eligible events with unchanged parent state; grants perfect prediction, not a finite archive bound.',arms=results,g_P=g,g_S=s,native_mutation_test_authorized=g>0 and s>0,standalone_decoder=False,parent_and_donor_trace_bytes=len(trace),dictionary_bytes=Path(dictionary).stat().st_size,complete_package_bytes=None,full_corpus_score_bytes=None,objective_credit_bytes=0,novel_algorithm_claim=False,verdict='A positive conditional finite replay authorizes one source-priced native mutation, not scale or score credit.' if g>0 and s>0 else 'This fixed calibrated continuation does not beat parent and shifted control; no native correction integration.')
    (out/'report.json').write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps({k:o[k] for k in ['active_bytes','perfect_ideal_upper_bits_ceil','g_P','g_S','native_mutation_test_authorized']}))
if __name__=='__main__':
    trace,stored,raw,dictionary,parent,coder,out=map(Path,sys.argv[1:])
    run(trace.read_bytes(),stored.read_bytes(),raw.read_bytes(),dictionary,parent.read_bytes(),coder.read_bytes(),out)
