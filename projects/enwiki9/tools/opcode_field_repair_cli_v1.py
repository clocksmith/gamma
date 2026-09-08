#!/usr/bin/env python3
"""Bounded command adapter and optional witnesses for the frozen field repair."""
from __future__ import annotations
import argparse
import errno
import hashlib
import importlib.util
import json
import marshal
from pathlib import Path
import resource
import sys
import time


def packed(value):
    # Version2 has no object-reference encoding: equal values hash equally even
    # when the two processes have different object aliasing or allocation order.
    return marshal.dumps(value, 2)


def feed(hasher, value):
    data = packed(value)
    hasher.update(len(data).to_bytes(8, 'big'))
    hasher.update(data)


def gst(state):
    names = ('f', 'w', 'p', 'q', 'r', 's', 'c', 'pg', 'col', 'tail', 'word', 'slot', 'position')
    return tuple((k, bytes(v) if isinstance(v, bytearray) else v)
                 for k in names for v in (getattr(state, k),))


def table_hash(hasher, name, table, value=lambda x: x, include=lambda x: True):
    feed(hasher, name)
    for key in sorted(table, key=packed):
        row = table[key]
        if include(row):
            feed(hasher, (key, value(row)))


class CountedHash:
    def __init__(self, seed):
        self.hash = hashlib.sha256(seed)
        self.bytes = len(seed)

    def update(self, data):
        self.hash.update(data)
        self.bytes += len(data)

    def hexdigest(self):
        return self.hash.hexdigest()


class Audit:
    def __init__(self, arm):
        self.arm = arm
        self.prob = hashlib.sha256(b'opcode-probabilities-v1')
        self.trans = hashlib.sha256(b'opcode-transitions-v1')
        self.arith = hashlib.sha256(b'opcode-arithmetic-v1')
        self.bits = self.events = self.bytes = 0
        self.fields = [0] * 7
        self.checkpoints = []

    def probability(self, event):
        feed(self.prob, event)
        self.bits += event[0] == 0

    def transition(self, event):
        feed(self.trans, event)

    def arithmetic(self, event):
        feed(self.arith, event)
        self.events += 1

    def checkpoint(self):
        return dict(modeled_bytes=self.bytes, predictor_bits=self.bits, arithmetic_events=self.events,
                    probability_sha256=self.prob.hexdigest(), transition_sha256=self.trans.hexdigest(),
                    arithmetic_sha256=self.arith.hexdigest())

    def byte(self, state, byte):
        self.bytes += 1
        self.fields[state.f] += 1
        # Sidecar state is predictive only in D. K must project to unchanged P.
        semantic = (state.field.f, state.field.pending) if self.arm == 'D' else None
        feed(self.trans, (4, byte, gst(state), semantic))
        if self.bytes % 4096 == 0:
            self.checkpoints.append(self.checkpoint())

    def finish(self, ns, coder, literal, state, tokens, chains, history):
        terminal = CountedHash(b'opcode-terminal-common-v1')
        feed(terminal, gst(state))
        feed(terminal, (state.field.f, state.field.pending) if self.arm == 'D' else None)
        feed(terminal, (coder.l, coder.h, coder.p, tokens.last, hashlib.sha256(history).digest()))
        for i, table in enumerate(literal.tt):
            table_hash(terminal, ('literal', i), table, tuple)
        table_hash(terminal, 'weights', literal.W, tuple)
        table_hash(terminal, 'sse', literal.sse, tuple)
        for name in ('e', 'rl', 'rd', 'clv', 'cix', 'cln'):
            # Cost-only probes allocate pristine count rows on the encoder.
            # An absent row and an all-one row have identical future behavior.
            table_hash(terminal, ('tokens', name), getattr(tokens, name),
                       lambda model: (tuple(model.c), model.t),
                       lambda model: model.t != len(model.c) or any(c != 1 for c in model.c))
        table_hash(terminal, 'ordered_chains', chains, tuple)
        if not self.checkpoints or self.checkpoints[-1]['modeled_bytes'] != self.bytes:
            self.checkpoints.append(self.checkpoint())
        return dict(schema='gamma.enwiki9.opcode-field-audit.v1',
                    lookup_tables_sha256=hashlib.sha256(packed((ns['_ST'], ns['_SQ']))).hexdigest(),
                    probability_sha256=self.prob.hexdigest(), transition_sha256=self.trans.hexdigest(),
                    arithmetic_sha256=self.arith.hexdigest(), terminal_common_state_sha256=terminal.hexdigest(),
                    terminal_common_state_bytes=terminal.bytes,
                    parent_projection_sha256=terminal.hexdigest(), modeled_bytes=self.bytes,
                    predictor_bits=self.bits, arithmetic_events=self.events, field_byte_counts=self.fields,
                    checkpoints=self.checkpoints,
                    witness_scope='All shared prediction/update events; final shared state. SHA256 witnesses, not full intermediate snapshots.',
                    excluded_state=['Encoder prefix-cost pass and raw-match search table',
                                    'Pristine cost-only count allocations',
                                    'Direction-specific arithmetic IO; decoder shadow verifies canonical payload'],
                    initialization='Authenticated parent source defaults and explicit arm field policy')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('encode', 'decode', 'legacy-encode'))
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--candidate-root', type=Path, required=True)
    parser.add_argument('--arm', choices=('P', 'K', 'D'), default='P')
    parser.add_argument('--audit', type=Path, required=True)
    args = parser.parse_args(argv)
    start, cpu = time.monotonic(), time.process_time()
    spec = importlib.util.spec_from_file_location('bound_field_codec', args.candidate_root/'field_codec.py')
    codec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(codec)
    codec.require(not args.output.exists() and not args.audit.exists(), 'output already exists')
    limit = codec.MAX_ARCHIVE if args.operation == 'decode' else codec.MAX_RAW
    codec.require(args.input.stat().st_size <= limit, 'input exceeds bound')
    raw = args.input.read_bytes()
    if args.operation == 'legacy-encode':
        out = codec.untouched(args.candidate_root)['compress'](raw)
        report = dict(archive_bytes=len(out), archive_sha256=codec.digest(out), raw_bytes=len(raw),
                      raw_sha256=codec.digest(raw), audit=dict(uninstrumented_parent=True))
    else:
        operation = codec.encode if args.operation == 'encode' else codec.decode
        out, report = operation(raw, args.arm, candidate_root=args.candidate_root, audit=Audit(args.arm))
    with args.output.open('xb') as stream:
        stream.write(out)
    with args.audit.open('x') as stream:
        json.dump(report['audit'], stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps(dict(result=report, cpu_seconds=time.process_time()-cpu,
                         elapsed_seconds=time.monotonic()-start,
                         peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss), sort_keys=True))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (MemoryError, OSError, ValueError) as error:
        budget = isinstance(error, MemoryError) or isinstance(error, OSError) and error.errno in (errno.EFBIG, errno.ENOMEM)
        print(json.dumps(dict(error_class='budget-exhausted' if budget else 'infrastructure-failure'
                              if isinstance(error, OSError) else 'implementation-failure',
                              error_type=type(error).__name__, error=str(error))), file=sys.stderr)
        raise SystemExit(1)
