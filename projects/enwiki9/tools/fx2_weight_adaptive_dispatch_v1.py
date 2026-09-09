#!/usr/bin/env python3
"""Emit the production dispatch repair without changing retained native source."""
import argparse
import hashlib
import json
from pathlib import Path

PARENT_SHA256 = '0166dd25bcd182e488261518eb42fa4cba0284d8f2e684e06a9c48325a7a01ab'


def patch(source):
    if hashlib.sha256(source).hexdigest() != PARENT_SHA256:
        raise ValueError('production dispatcher parent differs')
    old = b'                    std::memcmp(magic, "GFX2MAR1", 8) == 0)'
    new = (b'                    std::memcmp(magic, "GFX2MAR1", 8) == 0 ||\n'
           b'                    std::memcmp(magic, "GFX2ADM1", 8) == 0)')
    if source.count(old) != 1:
        raise ValueError('dispatch edit is not unique')
    return source.replace(old, new)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    data = patch(Path(args.source).read_bytes())
    with Path(args.output).open('xb') as stream:
        stream.write(data)
    print(json.dumps({'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                      'parent_sha256': PARENT_SHA256, 'objective_credit_bytes': 0}))


if __name__ == '__main__':
    main()
