#!/usr/bin/env python3
"""External witnesses for compact field repair; no model or probability changes."""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from opcode_field_repair_cli_v1 import Audit


def load(path):
    spec = importlib.util.spec_from_file_location('compact_bound_loader', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def observe(ns, audit):
    """Wrap the actual compact namespace, preserving its class implementations."""
    BaseGST, BaseLIT, BaseCM, BaseTOK, BaseAC = [ns[k] for k in ('GST', 'LIT', 'CM', 'TOK', 'AC')]
    base_add = ns['addc']

    class State(BaseGST):
        def up(self, byte):
            super().up(byte)
            audit.byte(self, byte)

    class Literal(BaseLIT):
        def predict(self, state, prefix, bit_index):
            values = super().predict(state, prefix, bit_index)
            pf, keys, bucket, mixed, stretches, weights = values
            audit.probability((0, state.position, prefix, bit_index, pf, tuple(keys), bucket,
                               mixed, tuple(stretches), tuple(weights)))
            return values

        def update(self, keys, bucket, mixed, stretches, weights, bit):
            super().update(keys, bucket, mixed, stretches, weights, bit)
            audit.transition((0, bit, tuple((i, key, tuple(self.tt[i][key])) for i, key in enumerate(keys)),
                              bucket, tuple(self.sse[bucket]), tuple(weights)))

    class Count(BaseCM):
        def cf(self, value):
            audit.probability((1, self.where, tuple(self.c), self.t))
            return super().cf(value)

        def find(self, target):
            audit.probability((1, self.where, tuple(self.c), self.t))
            return super().find(target)

        def up(self, value):
            super().up(value)
            audit.transition((1, self.where, value, tuple(self.c), self.t))

    class Tokens(BaseTOK):
        def m(self, table, key, size):
            model = super().m(table, key, size)
            model.where = (next(i for i, name in enumerate(('e', 'rl', 'rd', 'clv', 'cix', 'cln'))
                                if getattr(self, name) is table), key)
            return model

        def __setattr__(self, name, value):
            super().__setattr__(name, value)
            if name == 'last':
                audit.transition((2, value))

    class Coder(BaseAC):
        def enc(self, cumulative, frequency, total):
            before = (self.l, self.h)
            super().enc(cumulative, frequency, total)
            audit.arithmetic((cumulative, frequency, total, before, (self.l, self.h, self.p)))

        def dec(self, cumulative, frequency, total):
            before = (self.l, self.h)
            super().dec(cumulative, frequency, total)
            audit.arithmetic((cumulative, frequency, total, before,
                              (self.l, self.h, self.shadow.p)))

    def add_chain(table, state, position):
        update = tuple((key, tuple(table.get(key, ())[:-63])) for key in state.keys())
        base_add(table, state, position)
        audit.transition((3, position, update))

    captured = {}

    def capture(coder, literal, state, tokens, chains, history):
        captured['audit'] = audit.finish(ns, coder if coder.shadow is None else coder.shadow,
                                         literal, state, tokens, chains, history)

    original_prefix = ns['lit_prefix']

    def prefix(data):
        # The estimator has its own models and never enters common witnesses.
        # A separate globals mapping keeps the unobserved compact classes while
        # preserving the same compiled prefix body and constants.
        import types
        plain = dict(ns, GST=BaseGST, LIT=BaseLIT, CM=BaseCM, TOK=BaseTOK, AC=BaseAC, addc=base_add)
        return types.FunctionType(original_prefix.__code__, plain)(data)

    ns.update(GST=State, LIT=Literal, CM=Count, TOK=Tokens, AC=Coder,
              addc=add_chain, _capture=capture, lit_prefix=prefix)
    return captured


def execute(module, operation, data, observed=True):
    ns = module.namespace()
    captured = observe(ns, Audit('D')) if observed else None
    out = ns['compress' if operation == 'encode' else 'decompress'](data)
    return out, captured['audit'] if captured is not None else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('encode', 'decode'))
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--candidate-root', type=Path, required=True)
    parser.add_argument('--audit', type=Path)
    args = parser.parse_args()
    start, cpu = time.monotonic(), time.process_time()
    limit = 1000000 if args.operation == 'encode' else 33554432
    if args.input.stat().st_size > limit:
        raise ValueError('input exceeds bound')
    if args.output.exists() or args.audit is not None and args.audit.exists():
        raise ValueError('output already exists')
    out, audit = execute(load(args.candidate_root / 'program.py'), args.operation,
                         args.input.read_bytes(), args.audit is not None)
    with args.output.open('xb') as stream:
        stream.write(out)
    if args.audit is not None:
        with args.audit.open('x') as stream:
            json.dump(audit, stream, indent=2, sort_keys=True)
            stream.write('\n')
    print(json.dumps({'output_bytes': len(out), 'cpu_seconds': time.process_time()-cpu,
                      'elapsed_seconds': time.monotonic()-start,
                      'peak_process_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}, sort_keys=True))


if __name__ == '__main__':
    main()
