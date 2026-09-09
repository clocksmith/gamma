#!/usr/bin/env python3
"""Replay a closed ratio experiment; no predictor mutation or corpus launch."""
import argparse
import json
import math
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parents[1]))
sys.path.insert(0,str(ROOT/'tests'))
from test_fx2_residual_ratio_native_v1 import Native, load_library, bits, value
from fx2_weight_width_carry_model_v1 import verify


def converted(halves):
    """Reproduce the existing 205-wide native conversion, including its tail."""
    if len(halves)!=205:
        raise ValueError('half alphabet differs')
    result=[]
    floor=value(bits(1e-6))
    for i,h in enumerate(halves):
        p=struct.unpack('<e',struct.pack('<H',h))[0]
        if i>=200 and h & 0x7c00 == 0 and h & 1023:
            p*=0.5
        result.append(bits(p if p>=floor else floor))
    return result


def coder_comparison(parent,treatment,rows):
    a,b=Path(parent).read_bytes(),Path(treatment).read_bytes()
    if len(a)!=rows*8*28 or len(b)!=len(a):
        raise ValueError('coder length differs')
    raw=bytearray();per_byte=[];changed=0
    left=struct.iter_unpack('<7I',a);right=struct.iter_unpack('<7I',b)
    for _ in range(rows):
        byte=0;gain=0.0
        for _ in range(8):
            p,q=next(left),next(right)
            if p[6]!=q[6] or p[6]>1 or not (1<=p[1]<65536 and 1<=q[1]<65536):
                raise ValueError('coder truth or probability differs')
            byte=byte*2+p[6]
            pp=p[1] if p[6] else 65536-p[1]
            qq=q[1] if q[6] else 65536-q[1]
            gain+=math.log2(qq/pp);changed+=p[1]!=q[1]
        raw.append(byte);per_byte.append(gain)
    return bytes(raw),per_byte,changed


def replay(half_path,parent,treatment,state_path,vocabulary,library,rows):
    if len(vocabulary)!=205 or vocabulary!=sorted(set(vocabulary)) or any(not 0<=v<=255 for v in vocabulary):
        raise ValueError('vocabulary differs')
    raw,final_gain,changed=coder_comparison(parent,treatment,rows)
    mapping={b:i for i,b in enumerate(vocabulary)}
    if any(b not in mapping for b in raw):
        raise ValueError('truth outside vocabulary')
    ratio=Native(load_library(library),205,'D')
    expert_gain=[];base_loss=[];corrected_loss=[];state_records=0
    thirds=[dict(expert_bits_saved=0.0,final_coder_bits_saved=0.0,scored_symbols=0) for _ in range(3)]
    try:
        with Path(half_path).open('rb') as halves,Path(state_path).open('rb') as states:
            def check_state(kind):
                nonlocal state_records
                expected=ratio.serialize()
                if states.read(5)!=kind+struct.pack('<I',len(expected)) or states.read(len(expected))!=expected:
                    raise ValueError('first calibration-state divergence at record '+str(state_records))
                state_records+=1

            def half_row(kind,index):
                record=halves.read(421)
                if len(record)!=421 or record[0] not in kind or struct.unpack('<HQ',record[1:11])!=(205,index):
                    raise ValueError('half event order differs at row '+str(index))
                return struct.unpack('<205H',record[11:])

            check_state(b'I');previous=None
            for i,byte in enumerate(raw):
                third=min(2,i*3//rows)
                thirds[third]['final_coder_bits_saved']+=final_gain[i]
                if previous is not None:
                    p,q=previous;symbol=mapping[byte]
                    lp=-math.log2(p[symbol]/sum(p));lq=-math.log2(q[symbol]/sum(q))
                    base_loss.append(lp);corrected_loss.append(lq);expert_gain.append(lp-lq)
                    thirds[third]['expert_bits_saved']+=lp-lq;thirds[third]['scored_symbols']+=1
                    ratio.observe(symbol);check_state(b'O')
                half_row(b'I',i)
                base=converted(half_row(b'OF',i))
                corrected=ratio.predict(base);check_state(b'P')
                previous=([value(x) for x in base],[value(x) for x in corrected])
            if halves.read(1) or states.read(1):
                raise ValueError('trailing trace bytes')
    finally:
        ratio.close()
    return dict(schema='gamma.enwiki9.ratio-loss-attribution.v1',rows=rows,
                scored_symbols=len(expert_gain),matched_calibration_states=state_records,
                expert_parent_ideal_bits=math.fsum(base_loss),expert_treatment_ideal_bits=math.fsum(corrected_loss),
                expert_ideal_bits_saved=math.fsum(expert_gain),
                final_coder_ideal_bits_saved=math.fsum(final_gain),changed_q16_events=changed,
                chronological_thirds=thirds,initial_byte_unscored_by_expert=True,
                final_prediction_unconsumed=True,objective_credit_bytes=0,full_corpus_score_bytes=None)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('plan','inputs','output'):
        parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    plan=json.loads(Path(args.plan).read_text());inputs=json.loads(Path(args.inputs).read_text())
    verify(inputs['inputs']);verify(list(plan['files'].values()))
    f={k:ROOT/v['path'] for k,v in plan['files'].items()}
    if f['parent_coder'].read_bytes()!=f['half_parent_coder'].read_bytes():
        raise ValueError('parent trajectories differ across retained experiments')
    vocabulary=json.loads(f['vocabulary'].read_text())['vocabulary_bytes']
    result=replay(f['half'],f['parent_coder'],f['treatment_coder'],f['state'],vocabulary,f['library'],plan['rows'])
    if result['changed_q16_events']!=64583 or abs(result['final_coder_ideal_bits_saved']+1.7474386861516857)>1e-6:
        raise ValueError('retained final-loss reference differs')
    verify(inputs['inputs']);verify(list(plan['files'].values()))
    with Path(args.output).open('x') as stream:
        stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    main()
