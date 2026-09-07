#!/usr/bin/env python3
"""Decode an explicitly identified D2GRAM01 or D2GRAM02 archive."""
import argparse
import json
from pathlib import Path
import resource
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import dualstream_grammar_v1 as old
from tools import dualstream_grammar_argtokens_v2 as new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['decode'])
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    begin, cpu = time.monotonic(), time.process_time()
    with args.input.open('rb') as source:
        archive = source.read(old.MAX_ARCHIVE + 1)
    old.require(len(archive) <= old.MAX_ARCHIVE, 'input bound')
    codec = {old.MAGIC: old, new.MAGIC: new}.get(archive[:8])
    old.require(codec is not None, 'unrecognized grammar frontend')
    raw = codec.decode(archive)
    old.new_file(args.output, lambda stream: stream.write(raw))
    print(json.dumps(dict(result=dict(raw_bytes=len(raw), frontend=archive[:8].decode('ascii')),
                         cpu_seconds=time.process_time()-cpu, elapsed_seconds=time.monotonic()-begin,
                         peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                         complete_package_bytes=None, full_corpus_score_bytes=None)))


if __name__ == '__main__':
    main()
