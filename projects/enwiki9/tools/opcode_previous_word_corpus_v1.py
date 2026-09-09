#!/usr/bin/env python3
"""Bounded previous-word encode/decode with the same selected arm on both sides."""
import argparse
import json
from pathlib import Path
import resource
import struct
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from opcode_previous_word_observe_v1 import execute as observe_execute, load

RAW_LIMIT = 250000
ARCHIVE_LIMIT = 32 * 1024**2


def execute(module, operation, data, arm, observed=True):
    if operation not in ('encode', 'decode') or type(data) is not bytes:
        raise ValueError('invalid operation or input')
    if len(data) > (RAW_LIMIT if operation == 'encode' else ARCHIVE_LIMIT):
        raise ValueError('input exceeds frozen bound')
    if operation == 'decode':
        if len(data) < 9:
            raise ValueError('truncated archive')
        raw, modeled = struct.unpack('>II', data[:8])
        if raw > RAW_LIMIT or modeled > 2 * raw:
            raise ValueError('declared output exceeds frozen bound')
    output, audit = observe_execute(module, operation, data, arm, observed)
    if len(output) > (RAW_LIMIT if operation == 'decode' else ARCHIVE_LIMIT):
        raise ValueError('output exceeds frozen bound')
    return output, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('encode', 'decode'))
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--candidate-root', type=Path, required=True)
    parser.add_argument('--arm', choices=tuple('PKDS'), required=True)
    parser.add_argument('--audit', type=Path)
    args = parser.parse_args()
    limit = RAW_LIMIT if args.operation == 'encode' else ARCHIVE_LIMIT
    if args.input.stat().st_size > limit:
        raise ValueError('input exceeds frozen bound')
    if args.output.exists() or args.audit is not None and args.audit.exists():
        raise ValueError('output already exists')
    start, cpu = time.monotonic(), time.process_time()
    output, audit = execute(load(args.candidate_root / 'program.py'), args.operation,
                            args.input.read_bytes(), args.arm, args.audit is not None)
    with args.output.open('xb') as stream:
        stream.write(output)
    if args.audit is not None:
        with args.audit.open('x') as stream:
            json.dump(audit, stream, sort_keys=True, indent=2)
            stream.write('\n')
    print(json.dumps(dict(output_bytes=len(output), cpu_seconds=time.process_time()-cpu,
                         elapsed_seconds=time.monotonic()-start,
                         peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))


if __name__ == '__main__':
    main()
