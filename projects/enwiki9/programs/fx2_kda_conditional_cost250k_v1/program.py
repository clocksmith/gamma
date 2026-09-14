#!/usr/bin/env python3
"""Attribute fixed native trajectories; no new codec or free trace dependency."""
import json
import math
from pathlib import Path
import struct

from lib.fx2_closing_cost_v1 import ceiling_ratio
from tools.wrt_exact import parse_store_bytes, read_dictionary_words

VOCAB = bytes([232,22,4,0,255,255,255,3,1,252,15,249,254,255,255,7]+[255]*16)
TOKENS = [b for b in range(256) if VOCAB[b//8] & (1 << (b%8))]
SEPARATOR = bytes(TOKENS[t] for t in [8,8,37,172,101,39,5,8,8,8,8,37,172,104,39])
AGE_LIMITS = [1,4,16,64,256,1024]

def age_bin(age):
    return next((i for i,n in enumerate(AGE_LIMITS) if age<n),len(AGE_LIMITS))

def pieces(body,separator=SEPARATOR,maximum=131072):
    if not body or not separator or maximum<1:raise ValueError('invalid boundary inputs')
    starts=[0];count=0
    for i in range(len(body)):
        count+=1
        if count==maximum or body[max(0,i+1-len(separator)):i+1]==separator:
            count=0
            if i+1<len(body):starts.append(i+1)
    return starts

class Certificate:
    def __init__(self):self.n=self.d=1;self.events=0;self.chunks=[]
    def add(self,n,d):
        if not 0<d<=n:raise ValueError('invalid oracle mass ratio')
        if n==d:return
        self.n*=n;self.d*=d;self.events+=1
        if self.events==4096:self.flush()
    def flush(self):
        if not self.events:return
        self.chunks.append(dict(events=self.events,ceiling_bits=ceiling_ratio(self.n,self.d)))
        self.n=self.d=1;self.events=0
    def result(self):
        self.flush()
        return dict(chunks=self.chunks,ceiling_bits=sum(r['ceiling_bits'] for r in self.chunks))

def analyze(body,traces):
    if set(traces)!={'P','D','S'} or any(len(v)!=len(body)*8*28 for v in traces.values()):
        raise ValueError('trace coordinates differ')
    starts=pieces(body);ends=starts[1:]+[len(body)]
    rows=[];cost={a:[] for a in traces};gains={a:[] for a in ['D','S']}
    oracle_pd=[];oracle_pds=[];cert_pd=Certificate();cert_pds=Certificate()
    groups=[dict(D=[],S=[]) for _ in range(7)];changed={a:0 for a in ['D','S']}
    part=0;per_piece={a:[] for a in ['D','S']};piece_cost={a:[] for a in traces}
    for i,byte in enumerate(body):
        byte_cost={a:[] for a in traces};byte_gain={a:[] for a in ['D','S']};opd=[];opds=[]
        for bit in range(8):
            masses={};truth=(byte>>(7-bit))&1
            for a in traces:
                row=struct.unpack_from('<7I',traces[a],(i*8+bit)*28)
                if not 1<=row[1]<=65535 or row[6]!=truth:raise ValueError('invalid truth/count at '+str(i*8+bit))
                masses[a]=row[1] if truth else 65536-row[1]
                byte_cost[a].append(16-math.log2(masses[a]))
            for a in ['D','S']:
                value=math.log2(masses[a]/masses['P']);byte_gain[a].append(value)
                changed[a]+=masses[a]!=masses['P']
            best_pd=max(masses['P'],masses['D']);best_pds=max(masses.values())
            cert_pd.add(best_pd,masses['P']);cert_pds.add(best_pds,masses['P'])
            opd.append(math.log2(best_pd/masses['P']));opds.append(math.log2(best_pds/masses['P']))
        oracle_pd.append(math.fsum(opd));oracle_pds.append(math.fsum(opds))
        bucket=age_bin(i-starts[part])
        for a in traces:
            value=math.fsum(byte_cost[a]);cost[a].append(value);piece_cost[a].append(value)
        for a in ['D','S']:
            value=math.fsum(byte_gain[a]);gains[a].append(value);per_piece[a].append(value);groups[bucket][a].append(value)
        if i+1==ends[part]:
            rows.append(dict(piece=part,first_modeled_byte=starts[part],end_modeled_byte=i+1,
                previous_completed_piece_bytes=starts[part]-starts[part-1] if part else None,
                ideal_bits={a:math.fsum(piece_cost[a]) for a in traces},
                ideal_bits_saved={a:math.fsum(per_piece[a]) for a in ['D','S']}))
            part+=1;per_piece={a:[] for a in ['D','S']};piece_cost={a:[] for a in traces}
    pd=cert_pd.result();pds=cert_pds.result()
    require=lambda ok:None if ok else (_ for _ in ()).throw(ValueError('ceiling violated'))
    require(math.fsum(oracle_pd)<=pd['ceiling_bits']+1e-8)
    require(math.fsum(oracle_pds)<=pds['ceiling_bits']+1e-8)
    buckets=[dict(age_min=0 if k==0 else AGE_LIMITS[k-1],age_end=AGE_LIMITS[k] if k<6 else None,
                  modeled_bytes=len(group['D']),ideal_bits_saved={a:math.fsum(group[a]) for a in ['D','S']}) for k,group in enumerate(groups)]
    return dict(modeled_bytes=len(body),bit_records=len(body)*8,piece_count=len(rows),pieces=rows,age_buckets=buckets,
        ideal_bits={a:math.fsum(cost[a]) for a in traces},ideal_bits_saved={a:math.fsum(gains[a]) for a in ['D','S']},
        changed_probability_records=changed,positive_D_pieces=sum(r['ideal_bits_saved']['D']>0 for r in rows),
        negative_D_pieces=sum(r['ideal_bits_saved']['D']<0 for r in rows),
        hindsight_piece_PD_ideal_gain_bits=math.fsum(max(0,r['ideal_bits_saved']['D']) for r in rows),
        hindsight_age_PD_ideal_gain_bits=math.fsum(max(0,r['ideal_bits_saved']['D']) for r in buckets),
        clairvoyant_bit_PD_ideal_gain_bits=math.fsum(oracle_pd),clairvoyant_bit_PDS_ideal_gain_bits=math.fsum(oracle_pds),
        PD_certificate=pd,PDS_certificate=pds)

def main():
    import sys
    root=Path(sys.argv[1]);out=Path(sys.argv[2]);native=root/'results/fx2_kda_carry_opening250k_v1/work/native'
    stored=(native/'population.stored').read_bytes();raw=(native/'population.raw').read_bytes()
    parsed=parse_store_bytes(stored,read_dictionary_words(native/'dictionary/english.dic'))
    if parsed.decoded!=raw or parsed.stream[5:]!=stored[10:]:raise ValueError('exact WRT inverse differs')
    body=stored[10:]
    report=analyze(body,{a:(native/(a+'-encode.coder')).read_bytes() for a in ['P','D','S']})
    if len(raw)!=250000 or report['modeled_bytes']!=151210 or report['piece_count']!=98:raise ValueError('frozen population or boundary count differs')
    report.update(schema='gamma.enwiki9.kda-conditional-cost.v1',raw_population='[0,250000)',raw_bytes=len(raw),
        exact_wrt_inverse=True,truth_alignment=True,new_native_compression_runs=0,archive_saving_bytes=None,
        complete_package_bytes=None,full_corpus_score_bytes=None,objective_credit_bytes=0,
        proof='For fixed supplied probability trajectories, selecting or convexly mixing P/D/S cannot assign more truth mass than their pointwise maximum. Exact integer product log ceilings bound ideal loss gain before any selector/model cost. This is not a finite-archive bound and does not cover changed feedback, new trajectories or a newly gated native reset.',
        causal_limit='Piece age and previous completed length are pre-truth coordinates. Choosing favorable bins/pieces after observing their losses is hindsight, not a causal compressor.',
        budget_floor_ideal_bits=4096,fixed_trajectory_selector_headroom_pass=report['PDS_certificate']['ceiling_bits']>4096)
    with out.open('x') as f:json.dump(report,f,indent=2,sort_keys=True);f.write('\n')

if __name__=='__main__':main()
