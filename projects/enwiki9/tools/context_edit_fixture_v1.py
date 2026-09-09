#!/usr/bin/env python3
"""Fresh-process synthetic context-edit codec fixture with explicit arm options."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.context_edit_fixture_v1 import Fixture, ARMS
from lib.predictor import encode, decode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('encode', 'decode'))
    parser.add_argument('arm', choices=ARMS)
    parser.add_argument('input')
    parser.add_argument('output')
    parser.add_argument('--audit', required=True)
    args = parser.parse_args()
    source = Path(args.input)
    if source.stat().st_size > (4096 if args.operation == 'encode' else 131072):
        raise ValueError('synthetic input exceeds bound')
    if Path(args.output).exists() or Path(args.audit).exists():
        raise ValueError('output targets must be new')
    data = source.read_bytes()
    fixture = Fixture(args.arm)
    if args.operation == 'encode':
        output = encode(data, fixture)
    else:
        output = decode(data, fixture, maximum_bytes=4096)
        if encode(output, Fixture(args.arm)) != data:
            raise ValueError('noncanonical or truncated fixture archive')
    with Path(args.output).open('xb') as stream:
        stream.write(output)
    with Path(args.audit).open('x') as stream:
        stream.write(json.dumps(fixture.witness(), indent=2) + '\n')
    print(json.dumps(dict(output_bytes=len(output),sha256=hashlib.sha256(output).hexdigest(),objective_credit_bytes=0)))


if __name__ == '__main__':
    main()
