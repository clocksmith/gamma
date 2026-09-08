#!/usr/bin/env python3
"""Causal WRT forced-bit opportunity audit over a retained native parent trace."""
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lib.wrt_support_v1 import WrtSupport
from tools.wrt_exact import parse_store_bytes,read_dictionary_words

PLAN='operations/provenance/fx2_wrt_support_audit_v1_plan.json'
PARENT='results/fx2_cmix_transformer_static_vocab_fixture50051_q0_v1/work/'
TRACE='results/fx2_half_tail_fixture50051_q0_v1/work/P/encode.trace'


def audit():
    plan=json.loads((ROOT/PLAN).read_text())
    for row in plan['inputs']:
        p=ROOT/row['path']
        if p.stat().st_size!=row['bytes'] or hashlib.file_digest(p.open('rb'),'sha256').hexdigest()!=row['sha256']:
            raise ValueError('changed input: '+row['path'])
    stored=(ROOT/(PARENT+'fixture.stored')).read_bytes()
    parsed=parse_store_bytes(stored,read_dictionary_words(ROOT/(PARENT+'dictionary/english.dic')))
    raw=(ROOT/(PARENT+'prof_input/input')).read_bytes()
    if parsed.decoded!=raw:raise ValueError('WRT inverse differs from raw fixture')
    body=parsed.stream[5:]
    trace=(ROOT/TRACE).read_bytes()
    if len(body)!=32478 or len(trace)!=len(body)*8*28:raise ValueError('native coordinate length differs')
    state=WrtSupport();counts={};savings=[];parent_equal=0;forced=0
    for index,record in enumerate(struct.iter_unpack('<7I',trace)):
        p=record[1];truth=record[6]
        if not 0<p<65536 or truth!=((body[index//8]>>(7-index%8))&1):
            raise ValueError('native probability/truth coordinate differs')
        phase=state.phase
        choice=state.forced() # No access to this truth inside the automaton.
        if choice is not None:
            if choice!=truth:raise ValueError('automaton excluded actual truth')
            q=p if truth else 65536-p
            gain=math.log2(65535/q)
            forced+=1;parent_equal+=q==65535;savings.append(gain)
            row=counts.setdefault(phase,dict(forced_events=0,changed_events=0,ideal_saved_bits=0.0))
            row['forced_events']+=1;row['changed_events']+=q!=65535;row['ideal_saved_bits']+=gain
        state.observe(truth)
    state.finish()
    return dict(schema='gamma.enwiki9.wrt-support-audit.v1',status='passed',plan=PLAN,
                raw_bytes=len(raw),modeled_wrt_bytes=len(body),native_bit_records=len(trace)//28,
                exact_wrt_inverse=True,trace_truth_matches_store=True,all_truths_in_causal_support=True,
                forced_events=forced,already_maximal_parent_events=parent_equal,changed_probability_events=forced-parent_equal,
                ideal_saved_bits=math.fsum(savings),ideal_saved_bytes=math.fsum(savings)/8,
                states=counts,terminal_state_digest=state.state_digest(),
                archive_saving_bytes=None,complete_package_bytes=None,objective_credit_bytes=0,
                meaning='Conditional ideal gain on retained parent predictions, not a finite archive or native state-transfer certificate. Explicit one-TEXT-body frontend only; dictionary and parent remain required.',
                bound='At a proven forced truth,65535/65536 is no worse than any retained Q16 actual-bit probability. This proves nonnegative ideal gain for the fixed parent trajectory; coder termination and package costs require actual measurement.')


if __name__=='__main__':
    if len(sys.argv)!=1:raise SystemExit('no arguments expected')
    print(json.dumps(audit(),indent=2))
