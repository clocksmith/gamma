#!/usr/bin/env python3
"""Existing CLI/wrappers with witnesses for the reset-only decoder state."""
import hashlib
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import opcode_wiki_slot_observe_v1 as cli
from opcode_field_repair_cli_v1 import Audit, feed


class ResetAudit(Audit):
    def __init__(self):
        super().__init__('D')
        # Diagnostic comparator uses only decoded modeled bytes, no probabilities.
        parent=cli.load(ROOT/'programs/opcode_field_compact_v1/program.py').namespace()
        parent['_limit']=2000000
        self.baseline=parent['GST']()
        self.previous_pending=False
        self.previous_slot=0
        self.closes=self.effective_closes=0
        self.slots=[0]*10
        self.changed=0
        self.mode=None
        self.mode_slots=[[0]*10 for _ in range(3)]
        self.mode_changed=[0]*3

    def transition(self,event):
        super().transition(event)
        if event[0]==1 and event[1][0]==0:self.mode=event[2]

    def byte(self,state,byte):
        close=self.previous_pending and byte==2
        self.closes+=close
        self.effective_closes+=close and self.previous_slot!=0
        self.previous_pending=state.field.pending;self.previous_slot=state.slot
        self.baseline.up(byte)
        super().byte(state,byte)
        changed=state.slot!=self.baseline.slot
        self.changed+=changed;self.slots[state.slot]+=1
        if self.mode not in (0,1,2):raise ValueError('missing event mode')
        self.mode_changed[self.mode]+=changed;self.mode_slots[self.mode][state.slot]+=1

    def finish(self,ns,coder,literal,state,tokens,chains,history):
        parent=super().finish(ns,coder,literal,state,tokens,chains,history)
        final=hashlib.sha256(b'wiki-reset-terminal-v1')
        feed(final,(parent['terminal_common_state_sha256'],state.modeled_f))
        return dict(schema='gamma.enwiki9.opcode-slot-reset-audit.v1',parent=parent,
            complete_terminal_sha256=final.hexdigest(),slot_byte_counts=self.slots,
            changed_slot_bytes=self.changed,mode_slot_byte_counts=self.mode_slots,
            mode_changed_slot_bytes=self.mode_changed,modes=['literal','raw-copy','chain-copy'],
            complete_text_close_events=self.closes,nonzero_slot_before_close_events=self.effective_closes,
            counter_scope='Post-update occupancy against decoded compact-parent state; close counts do not assign predictive gain.')


def execute(module,operation,data,arm,observed=True):
    ns=module.namespace(arm)
    captured=cli.observe(ns,ResetAudit()) if observed else None
    out=ns['compress' if operation=='encode' else 'decompress'](data)
    return out,captured['audit'] if captured is not None else None


if __name__=='__main__':
    cli.execute=execute
    cli.main()
