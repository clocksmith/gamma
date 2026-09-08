#!/usr/bin/env python3
"""Observe existing mixed/calibrated probabilities without changing codec execution."""
import hashlib
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import opcode_field_compact_observe_v1 as parent
from opcode_field_repair_cli_v1 import Audit, feed


class CalibrationAudit(Audit):
    def __init__(self,total):
        super().__init__('D')
        self.total=total
        self.pending=None
        self.mode=None
        self.rows={}
        self.observed=0
        self.events_hash=hashlib.sha256(b'opcode-calibration-pretruth-v1')

    def probability(self,event):
        super().probability(event)
        if event[0]==0:
            if self.pending is not None:raise ValueError('prediction without prior truth update')
            self.pending=event

    def transition(self,event):
        super().transition(event)
        if event[0]==1 and event[1][0]==0:
            self.mode=event[2]
        if event[0]!=0:return
        if self.pending is None or self.mode not in (0,1,2):
            raise ValueError('truth without prediction or coded mode')
        pred=self.pending;self.pending=None
        _,position,prefix,index,pf,keys,bucket,pm,stretches,weights=pred
        bit=event[1]
        if bit not in (0,1) or not (0<pf<self.total and 0<pm<self.total):
            raise ValueError('invalid actual bit or probability')
        if (position,index)!=(self.observed//8,self.observed%8):
            raise ValueError('prediction coordinate skipped or duplicated')
        if bucket!=event[3] or keys!=tuple(x[1] for x in event[2]):
            raise ValueError('truth updates a different predictive context')
        q=pf if bit==0 else self.total-pf
        p=pm if bit==0 else self.total-pm
        key=(self.mode,bucket[2])
        row=self.rows.setdefault(key,dict(bits=0,changed_bits=0,mixed_loss_bits=0.0,
            calibrated_loss_bits=0.0,sse_excess_bits=0.0))
        row['bits']+=1;row['changed_bits']+=pf!=pm
        row['mixed_loss_bits']+=math.log2(self.total/p)
        row['calibrated_loss_bits']+=math.log2(self.total/q)
        row['sse_excess_bits']+=math.log2(p/q)
        feed(self.events_hash,(position,prefix,index,self.mode,bucket[2],pf,pm,bit))
        self.observed+=1

    def finish(self,ns,coder,literal,state,tokens,chains,history):
        common=super().finish(ns,coder,literal,state,tokens,chains,history)
        if self.pending is not None or self.observed!=8*len(history) or self.observed!=common['predictor_bits']:
            raise ValueError('missing diagnostic events')
        rows=[dict(mode=mode,field=field,**self.rows[(mode,field)]) for mode,field in sorted(self.rows)]
        return dict(schema='gamma.enwiki9.opcode-calibration-audit.v1',parent=common,
            diagnostic_event_sha256=self.events_hash.hexdigest(),observed_bits=self.observed,rows=rows,
            literal_sse_excess_bits=math.fsum(r['sse_excess_bits'] for r in rows if r['mode']==0),
            coded_literal_bits=sum(r['bits'] for r in rows if r['mode']==0),
            modes=['literal','raw-copy','chain-copy'],
            interpretation='Positive excess means calibration worsens fixed-parse literal log loss. Copied-bit losses are hypothetical. No counterfactual archive or rigorous rounding certificate.')


def execute(module,operation,data,observed=True):
    ns=module.namespace()
    captured=parent.observe(ns,CalibrationAudit(ns['T'])) if observed else None
    out=ns['compress' if operation=='encode' else 'decompress'](data)
    return out,captured['audit'] if captured is not None else None


if __name__=='__main__':
    parent.execute=execute
    parent.main()
