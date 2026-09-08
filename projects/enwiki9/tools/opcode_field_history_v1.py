#!/usr/bin/env python3
"""Standalone parent loading and existing witnesses for the history experiment."""
import argparse
import hashlib
import json
import lzma
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from lib.opcode_field_history_v1 import install, side_state
from opcode_field_compact_observe_v1 import observe
from opcode_field_repair_cli_v1 import Audit, feed, packed

PARENT = ROOT / 'programs/opcode_field_compact_v1/p'
PARENT_SHA = '7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8'


def namespace(arm='D'):
    source = PARENT.read_bytes()
    if hashlib.sha256(source).hexdigest() != PARENT_SHA:
        raise ValueError('parent source identity differs')
    ns = {'__name__': 'opcode_field_history'}
    exec(compile(lzma.decompress(source), '<authenticated-parent>', 'exec'), ns)
    return install(ns, arm)


class HistoryAudit(Audit):
    def __init__(self):
        super().__init__('D')  # All arms retain the confirmed parent field repair.
        self.side = hashlib.sha256(b'opcode-field-history-v1')
        self.side_checkpoints = []

    def byte(self, state, byte):
        super().byte(state, byte)
        feed(self.side, (state.position, state.modeled_f, side_state(state)))
        if self.bytes % 4096 == 0:
            self.side_checkpoints.append((self.bytes, self.side.hexdigest()))

    def finish(self, ns, coder, literal, state, tokens, chains, history):
        parent = super().finish(ns, coder, literal, state, tokens, chains, history)
        final = hashlib.sha256(b'opcode-field-history-terminal-v1')
        feed(final, (parent['terminal_common_state_sha256'], state.modeled_f, side_state(state)))
        if not self.side_checkpoints or self.side_checkpoints[-1][0] != self.bytes:
            self.side_checkpoints.append((self.bytes, self.side.hexdigest()))
        return dict(schema='gamma.enwiki9.opcode-field-history-audit.v1', parent=parent,
                    complete_terminal_sha256=final.hexdigest(), side_state_sha256=self.side.hexdigest(),
                    side_checkpoints=self.side_checkpoints, terminal_side_state_hex=packed(side_state(state)).hex(),
                    field_entries=getattr(state, 'entries', None), body_bytes=getattr(state, 'body_bytes', None),
                    witness_scope='Every existing shared prediction/update/coder event and every introduced history update; final complete shared state, represented by SHA256 witnesses')


def execute(operation, data, arm, observed=True):
    ns = namespace(arm)
    captured = observe(ns, HistoryAudit()) if observed else None
    output = ns['compress' if operation == 'encode' else 'decompress'](data)
    return output, captured['audit'] if captured is not None else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('encode', 'decode'))
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--arm', choices=('P', 'K', 'D', 'G', 'S'), required=True)
    parser.add_argument('--audit', type=Path)
    args = parser.parse_args()
    if args.input.stat().st_size > (8192 if args.operation == 'encode' else 33554432):
        raise ValueError('synthetic input cap exceeded')
    if args.output.exists() or args.audit is not None and args.audit.exists():
        raise ValueError('output already exists')
    start, cpu = time.monotonic(), time.process_time()
    output, audit = execute(args.operation, args.input.read_bytes(), args.arm, args.audit is not None)
    with args.output.open('xb') as f:
        f.write(output)
    if args.audit is not None:
        with args.audit.open('x') as f:
            json.dump(audit, f, sort_keys=True, indent=2)
            f.write('\n')
    print(json.dumps(dict(output_bytes=len(output), elapsed_seconds=time.monotonic()-start,
                          cpu_seconds=time.process_time()-cpu,
                          peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))


if __name__ == '__main__':
    main()
