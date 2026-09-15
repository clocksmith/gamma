"""Conditional finite archives for expert legal-mass likelihood correction."""
import hashlib
import json
import math
import mmap
from pathlib import Path
import struct
import sys

from lib.fx2_wrt_elision_v1 import Grammar
from lib.fx2_wrt_mass_v1 import row_masses, prefixes, correct
from tools.causal_field_parent_coder_v1 import Encoder, Decoder
from tools.fx2_final_counts_replay_v1 import framing
from tools.wrt_exact import parse_store_bytes, read_dictionary_words

BASE='results/fx2_wrt_elision250k_v2/'
NEURAL='results/fx2_attention_window250k_v2/work/native/P-encode.probs'
DICTIONARY='results/fx2_residual_features250k_v3/work/native/dictionary/english.dic'


def digest(b): return hashlib.sha256(b).hexdigest()


def write(p,b):
    with p.open('xb') as f:f.write(b)


def report(p,r):write(p,(json.dumps(r,indent=2,sort_keys=True)+'\n').encode())


def feature_row(neural, byte_index, row_bytes):
    if byte_index < 1:return None
    start=(byte_index-1)*row_bytes
    row=neural[start:start+row_bytes]
    if len(row)!=row_bytes:raise ValueError('missing pre-truth neural row')
    return row


def project(root,out):
    meta=json.loads((root/(BASE+'projection.json')).read_text())
    body=(root/(BASE+'population.modeled')).read_bytes()
    counts=(root/(BASE+'parent.q16')).read_bytes();prefix=(root/(BASE+'prefix.bin')).read_bytes()
    if len(body)!=151210 or len(counts)!=8*len(body)*2 or meta['raw_bytes']!=250000:
        raise ValueError('fixed population differs')
    if digest(body)!=meta['modeled_sha256'] or digest(counts)!=meta['parent_count_sha256']:
        raise ValueError('retained count or body identity differs')
    raw_bytes,vocab=framing(prefix,len(body));vocab=sorted(vocab)
    words=read_dictionary_words(root/DICTIONARY)
    if len(words)!=meta['word_count'] or len(vocab)!=205:raise ValueError('format inputs differ')
    raw=parse_store_bytes(b'\x07'+raw_bytes.to_bytes(4,'big')+body,words).decoded
    if digest(raw)!=meta['raw_sha256']:raise ValueError('retained inverse differs')
    size=2*len(vocab);path=root/NEURAL
    if path.stat().st_size!=size*len(body):raise ValueError('neural row population differs')
    # Include the last, unused prediction in input validation, never in coding.
    with path.open('rb') as f:
        for _ in range(len(body)):row_masses(f.read(size),vocab)
    meta.update(neural_path=NEURAL,neural_bytes=path.stat().st_size,neural_sha256=digest(path.read_bytes()),
        dictionary_path=DICTIONARY,vocabulary=vocab,neural_rows=len(body),used_neural_rows=len(body)-1,
        orientation='Row i is available after input i, and is used only for byte i+1. Byte0 is forced mode7. Final row is unused.',
        word_count=len(words),objective_credit_bytes=0)
    for name,data in [('population.modeled',body),('parent.q16',counts),('prefix.bin',prefix)]:write(out/name,data)
    report(out/'projection.json',meta)


def replay(root,out,operation,arm):
    meta=json.loads((out/'projection.json').read_text());n=meta['modeled_bytes'];events=n*8
    counts=(out/'parent.q16').read_bytes();prefix=(out/'prefix.bin').read_bytes()
    if len(counts)!=2*events or digest(counts)!=meta['parent_count_sha256']:raise ValueError('count dependency differs')
    raw_bytes,vocab=framing(prefix,n);vocab=sorted(vocab)
    if vocab!=meta['vocabulary']:raise ValueError('vocabulary differs')
    words=read_dictionary_words(root/meta['dictionary_path']);g=Grammar(len(words),vocab)
    header=bytes([1,1]) if arm=='K' else bytes([2,0 if arm=='M' else 1])
    source=(out/(arm+'-encode.arc')).read_bytes() if operation=='decode' else (out/(arm+'-decode.modeled' if operation=='repeat' else 'population.modeled')).read_bytes()
    limit=16*n+1024;offset=len(header)+len(prefix)
    decoder=None
    if operation=='decode':
        if source[:offset]!=header+prefix:raise ValueError('archive header differs')
        decoder=Decoder(source[offset:],max_bits=events,max_payload_bytes=limit,
                        expected_payload_bytes=len(source)-offset,payload_sha256=digest(source[offset:]))
    elif len(source)!=n or digest(source)!=meta['modeled_sha256']:raise ValueError('input population differs')
    encoder=Encoder(max_bits=events,max_payload_bytes=limit)
    states=hashlib.sha256();states.update(g.state());actions=hashlib.sha256();features=hashlib.sha256()
    restored=bytearray(n);changed=skipped=0;thirds=[dict(changed_counts=0,ideal_gain_bits_diagnostic=0.0) for _ in range(3)]
    checkpoints=[];cdf=legal=None;path=root/meta['neural_path']
    if path.stat().st_size!=meta['neural_bytes']:raise ValueError('neural dependency length differs')
    with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as neural:
        if digest(neural)!=meta['neural_sha256']:raise ValueError('neural dependency hash differs')
        for i,(parent,) in enumerate(struct.iter_unpack('<H',counts)):
            if not 1<=parent<=65535:raise ValueError('invalid parent count')
            if i%8==0:
                row=feature_row(neural,i//8,2*len(vocab))
                if row is not None:
                    features.update(row)
                    cdf,legal=prefixes(row_masses(row,vocab,rotate=arm=='S'),g.allowed())
            forced=g.forced()
            if forced is None:
                if cdf is None:raise ValueError('missing causal expert')
                proposed=correct(parent,g.prefix,cdf,legal)
                count=parent if arm=='K' else proposed
                y=decoder.decode(count) if decoder else source[i//8]>>(7-i%8)&1
                encoder.encode(y,count)
                changed+=count!=parent
            else:
                count=0;y=forced;skipped+=1
                if not decoder and y!=(source[i//8]>>(7-i%8)&1):raise ValueError('invalid forced truth')
            if decoder and (encoder.low,encoder.high)!=(decoder.low,decoder.high):raise ValueError('independent arithmetic state differs')
            actual=parent if y else 65536-parent
            new=65536 if forced is not None else count if y else 65536-count
            t=thirds[min(2,i*3//events)];t['changed_counts']+=count!=parent and forced is None
            t['ideal_gain_bits_diagnostic']+=math.log2(new/actual)
            actions.update(struct.pack('<HHB',parent,count,y));g.observe(y)
            restored[i//8]=(restored[i//8]<<1)|y
            if i%8==7:states.update(g.state())
            if (i+1)%2048==0 or i+1==events:checkpoints.append([i+1,digest(g.state()),actions.hexdigest()])
    g.finish()
    if digest(restored)!=meta['modeled_sha256']:raise ValueError('modeled reconstruction differs')
    archive=header+prefix+encoder.finish()
    if decoder and archive!=source:raise ValueError('canonical arithmetic termination differs')
    raw=parse_store_bytes(b'\x07'+raw_bytes.to_bytes(4,'big')+restored,words).decoded
    if len(raw)!=meta['raw_bytes'] or digest(raw)!=meta['raw_sha256']:raise ValueError('raw inverse differs')
    if decoder:
        write(out/(arm+'-decode.modeled'),restored);write(out/(arm+'-decode.raw'),raw)
    else:write(out/(arm+'-'+operation+'.arc'),archive)
    result=dict(arm=arm,operation=operation,archive_bytes=len(archive),archive_sha256=digest(archive),
        raw_bytes=len(raw),raw_sha256=digest(raw),modeled_sha256=digest(restored),events=events,
        changed_counts=changed,elided_events=skipped,action_sha256=actions.hexdigest(),
        grammar_state_sha256=states.hexdigest(),final_state_sha256=digest(g.state()),
        causal_feature_sha256=features.hexdigest(),checkpoints=checkpoints,thirds=thirds,
        used_neural_rows=n-1,archive_header_bytes=2,exact_inverse=True,standalone_decoder=False,
        parent_count_dependency_bytes=len(counts),neural_dependency_bytes=meta['neural_bytes'],
        dictionary_dependency_bytes=(root/meta['dictionary_path']).stat().st_size,
        complete_package_bytes=None,full_corpus_score_bytes=None,objective_credit_bytes=0)
    report(out/(arm+'-'+operation+'.json'),result)
    print(json.dumps({k:result[k] for k in ['arm','operation','archive_bytes','changed_counts']}))


def main():
    root,out=map(Path,sys.argv[1:3]);operation=sys.argv[3]
    if operation=='project' and len(sys.argv)==4:project(root,out)
    elif operation in ('encode','decode','repeat') and len(sys.argv)==5 and sys.argv[4] in ('K','M','S'):replay(root,out,operation,sys.argv[4])
    else:raise ValueError('unsupported invocation')


if __name__=='__main__':main()
