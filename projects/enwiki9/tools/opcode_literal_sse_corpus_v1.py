#!/usr/bin/env python3
"""Native-arm decoding and separate witnesses for calibration and unchanged state."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from opcode_field_compact_observe_v1 import load
from opcode_field_repair_cli_v1 import Audit, feed


class CalibrationAudit(Audit):
    def __init__(self):
        super().__init__('D')
        self.base_prob = hashlib.sha256(b'literal-sse-base-prob-v1')
        self.base_trans = hashlib.sha256(b'literal-sse-base-trans-v1')
        self.parse = hashlib.sha256(b'literal-sse-parse-v1')
        self.parse_events = 0
        self.mode = None
        self.updates_by_mode = [0, 0, 0]

    def probability(self, event):
        super().probability(event)
        feed(self.base_prob, event[:4] + event[5:] if event[0] == 0 else event)

    def transition(self, event):
        super().transition(event)
        feed(self.base_trans, event[:4] + event[5:] if event[0] == 0 else event)
        if event[0] == 0:
            if self.mode not in (0, 1, 2):
                raise ValueError('literal update before decoded mode')
            self.updates_by_mode[self.mode] += 1

    def parsed(self, event):
        if event[0] == 0:
            self.mode = event[-1]
        feed(self.parse, event)
        self.parse_events += 1

    def finish(self, ns, coder, literal, state, tokens, chains, history):
        if getattr(literal, 'in_literal', False):
            raise ValueError('unfinished literal training mode')
        parent = super().finish(ns, coder, literal, state, tokens, chains, history)
        return dict(parent=parent, non_sse=dict(probability_sha256=self.base_prob.hexdigest(),
                    transition_sha256=self.base_trans.hexdigest()),
                    parse_sha256=self.parse.hexdigest(), parse_events=self.parse_events,
                    updates_by_mode=self.updates_by_mode)


def observe(ns):
    audit = CalibrationAudit()
    BaseTOK = ns['TOK']

    class Tokens(BaseTOK):
        def eve(self, coder, state, mode):
            audit.parsed((0, state.position, mode))
            return super().eve(coder, state, mode)
        def evd(self, coder, state):
            mode = super().evd(coder, state)
            audit.parsed((0, state.position, mode))
            return mode
        def rawe(self, coder, length, distance):
            audit.parsed((1, length, distance))
            return super().rawe(coder, length, distance)
        def rawd(self, coder):
            result = super().rawd(coder)
            audit.parsed((1,) + result)
            return result
        def chaine(self, coder, state, level, index, length):
            audit.parsed((2, level, index, length))
            return super().chaine(coder, state, level, index, length)
        def chaind(self, coder, state):
            result = super().chaind(coder, state)
            audit.parsed((2,) + result)
            return result

    ns['TOK'] = Tokens
    path = ROOT / 'tools/opcode_field_compact_observe_v1.py'
    source = path.read_text()
    old = 'tuple(self.sse[bucket])'
    if source.count(old) != 1:
        raise ValueError('observer SSE site differs')
    source = source.replace(old, 'None if bucket not in self.sse else tuple(self.sse[bucket])')
    observer_ns = dict(__name__='literal_sse_observer', __file__=str(path))
    exec(compile(source, str(path), 'exec'), observer_ns)
    return observer_ns['observe'](ns, audit)


def execute(module, operation, data, arm, observed=True):
    ns = module.namespace(arm)
    capture = observe(ns) if observed else None
    output = ns['compress' if operation == 'encode' else 'decompress'](data)
    return output, capture['audit'] if observed else None


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation', choices=('encode','decode'))
    p.add_argument('input', type=Path); p.add_argument('output', type=Path)
    p.add_argument('--candidate-root', type=Path, required=True)
    p.add_argument('--arm', choices=tuple('PKD'), required=True)
    p.add_argument('--audit', type=Path)
    args = p.parse_args()
    if args.input.stat().st_size > (250000 if args.operation == 'encode' else 33554432):
        raise ValueError('input bound')
    if args.output.exists() or args.audit is not None and args.audit.exists():
        raise ValueError('output exists')
    start, cpu = time.monotonic(), time.process_time()
    out, audit = execute(load(args.candidate_root/'program.py'), args.operation,
                         args.input.read_bytes(), args.arm, args.audit is not None)
    if args.operation == 'decode' and len(out) > 250000:
        raise ValueError('output bound')
    with args.output.open('xb') as f: f.write(out)
    if args.audit is not None:
        with args.audit.open('x') as f: json.dump(audit, f, indent=2, sort_keys=True); f.write('\n')
    print(json.dumps(dict(output_bytes=len(out), elapsed_seconds=time.monotonic()-start,
                         cpu_seconds=time.process_time()-cpu,
                         peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))


if __name__ == '__main__':
    main()
