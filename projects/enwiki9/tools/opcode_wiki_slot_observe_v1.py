#!/usr/bin/env python3
"""Reuse compact witnesses and additionally bind every reconstructed slot state."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from opcode_field_compact_observe_v1 import load, observe
from opcode_field_repair_cli_v1 import Audit, feed, packed


def side(state):
    if not hasattr(state, 'raw_state'):
        return None
    return (state.modeled_slot, state.raw_pending, state.raw_position,
            tuple((k, bytes(v) if isinstance(v, bytearray) else v)
                  for k, v in sorted(vars(state.raw_state).items())))


class SlotAudit(Audit):
    def __init__(self):
        super().__init__('D')  # Every arm retains the confirmed field repair.
        self.side_hash = hashlib.sha256(b'wiki-slot-side-v1')
        self.slots = [0]*10
        self.changed = 0
        self.side_checkpoints = []
        self.mode = None
        self.mode_slots = [[0]*10 for _ in range(3)]
        self.mode_changed = [0]*3

    def transition(self, event):
        super().transition(event)
        if event[0] == 1 and event[1][0] == 0:
            self.mode = event[2]

    def byte(self, state, byte):
        super().byte(state, byte)
        self.slots[state.slot] += 1
        self.changed += state.slot != getattr(state, 'modeled_slot', state.slot)
        if self.mode not in (0, 1, 2):
            raise ValueError('decoded byte lacks its event mode')
        self.mode_slots[self.mode][state.slot] += 1
        self.mode_changed[self.mode] += state.slot != getattr(state, 'modeled_slot', state.slot)
        feed(self.side_hash, (state.position, side(state), state.modeled_f))
        if self.bytes % 4096 == 0:
            self.side_checkpoints.append((self.bytes, self.side_hash.hexdigest()))

    def finish(self, ns, coder, literal, state, tokens, chains, history):
        parent = super().finish(ns, coder, literal, state, tokens, chains, history)
        final = hashlib.sha256(b'wiki-slot-terminal-v1')
        feed(final, (parent['terminal_common_state_sha256'], side(state), state.modeled_f))
        if not self.side_checkpoints or self.side_checkpoints[-1][0] != self.bytes:
            self.side_checkpoints.append((self.bytes, self.side_hash.hexdigest()))
        return dict(schema='gamma.enwiki9.opcode-wiki-slot-audit.v1', parent=parent,
                    complete_terminal_sha256=final.hexdigest(),
                    side_state_sha256=self.side_hash.hexdigest(),
                    side_checkpoints=self.side_checkpoints, terminal_side_state_hex=packed(side(state)).hex(),
                    slot_byte_counts=self.slots, changed_slot_bytes=self.changed,
                    mode_slot_byte_counts=self.mode_slots, mode_changed_slot_bytes=self.mode_changed,
                    modes=['literal', 'raw-copy', 'chain-copy'])


def execute(module, operation, data, arm, observed=True):
    ns = module.namespace(arm)
    audit = SlotAudit()
    captured = observe(ns, audit) if observed else None
    out = ns['compress' if operation == 'encode' else 'decompress'](data)
    return out, captured['audit'] if captured is not None else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('encode', 'decode'))
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--candidate-root', type=Path, required=True)
    parser.add_argument('--arm', choices=('P', 'K', 'D'), required=True)
    parser.add_argument('--audit', type=Path)
    args = parser.parse_args()
    start, cpu = time.monotonic(), time.process_time()
    limit = 250000 if args.operation == 'encode' else 33554432
    if args.input.stat().st_size > limit:
        raise ValueError('input exceeds gate bound')
    if args.output.exists() or args.audit is not None and args.audit.exists():
        raise ValueError('output already exists')
    out, audit = execute(load(args.candidate_root/'program.py'), args.operation,
                         args.input.read_bytes(), args.arm, args.audit is not None)
    with args.output.open('xb') as stream:
        stream.write(out)
    if args.audit is not None:
        with args.audit.open('x') as stream:
            json.dump(audit, stream, indent=2, sort_keys=True); stream.write('\n')
    print(json.dumps(dict(output_bytes=len(out), cpu_seconds=time.process_time()-cpu,
                          elapsed_seconds=time.monotonic()-start,
                          peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))


if __name__ == '__main__':
    main()
