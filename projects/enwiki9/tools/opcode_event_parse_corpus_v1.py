#!/usr/bin/env python3
"""Bounded event-pricing encode; every decode uses the original parent."""
import argparse
import json
from pathlib import Path
import resource
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from opcode_field_compact_observe_v1 import load, observe
from opcode_field_repair_cli_v1 import Audit


def execute(module, operation, data, arm, observed=True):
    ns = module.namespace('P' if operation == 'decode' else arm)
    captured = observe(ns, Audit('D')) if observed else None
    output = ns['compress' if operation == 'encode' else 'decompress'](data)
    return output, dict(parent=captured['audit']) if captured is not None else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('encode', 'decode'))
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--candidate-root', type=Path, required=True)
    parser.add_argument('--arm', choices=tuple('PKD'), required=True)
    parser.add_argument('--audit', type=Path)
    args = parser.parse_args()
    if args.input.stat().st_size > (250000 if args.operation == 'encode' else 33554432):
        raise ValueError('input exceeds frozen bound')
    if args.output.exists() or args.audit is not None and args.audit.exists():
        raise ValueError('output already exists')
    start, cpu = time.monotonic(), time.process_time()
    out, audit = execute(load(args.candidate_root / 'program.py'), args.operation,
                         args.input.read_bytes(), args.arm, args.audit is not None)
    if args.operation == 'decode' and len(out) > 250000:
        raise ValueError('reconstructed output exceeds frozen bound')
    with args.output.open('xb') as stream:
        stream.write(out)
    if args.audit is not None:
        with args.audit.open('x') as stream:
            json.dump(audit, stream, sort_keys=True, indent=2)
            stream.write('\n')
    print(json.dumps(dict(output_bytes=len(out), cpu_seconds=time.process_time()-cpu,
                         elapsed_seconds=time.monotonic()-start,
                         peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))


if __name__ == '__main__':
    main()
