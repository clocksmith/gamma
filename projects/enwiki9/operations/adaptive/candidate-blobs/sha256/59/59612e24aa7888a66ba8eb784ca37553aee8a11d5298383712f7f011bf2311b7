#!/usr/bin/env python3
"""Bounded raw forward/reverse blocks with unchanged standard-library BZip2."""
import argparse
import bz2
import hashlib
import json
import os
from pathlib import Path
import resource
import struct
import time

HEADER, FRAME = struct.Struct('<8sIIQ'), struct.Struct('<IIB32s')
MAGIC = b'D2REVB01'
MAX_RAW, MAX_BLOCK, MAX_ARCHIVE = 1000000, 250000, 8000000
TRANSFORM_SPEC = dict(block_bytes=250000, direction='whole-block-byte-reversal',
                      backend='stdlib-bzip2-level9', treatment='forced-reverse',
                      dictionary='none', independent_blocks=True)


class CodecError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise CodecError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def frame_report(raw, coded, size, direction):
    return dict(raw_bytes=len(raw), raw_sha256=sha(raw), output_sha256=sha(raw),
                direction=direction, complete_frame_bytes=FRAME.size + size,
                costs=dict(bz2_payload=size, framing=FRAME.size), coded_bytes_sha256=sha(coded))


def report(raw, archive, block_size, frames):
    return dict(raw_bytes=len(raw), raw_sha256=sha(raw), archive_sha256=sha(archive),
                complete_archive_bytes=len(archive), block_size=block_size, backend='bz2-9',
                costs=dict(bz2_payload=sum(f['costs']['bz2_payload'] for f in frames),
                           framing=HEADER.size + len(frames) * FRAME.size), frames=frames,
                complete_package_bytes=None, full_corpus_score_bytes=None)


def encode(raw, mode='D', block_size=MAX_BLOCK):
    require(isinstance(raw, bytes) and len(raw) <= MAX_RAW and mode in ('P', 'K', 'D')
            and type(block_size) is int and 1 <= block_size <= MAX_BLOCK, 'encoder input bound')
    count = (len(raw) + block_size - 1) // block_size
    require(HEADER.size + count * FRAME.size <= MAX_ARCHIVE, 'archive framing bound')
    output = bytearray(HEADER.pack(MAGIC, block_size, count, len(raw)))
    rows = []
    for start in range(0, len(raw), block_size):
        part = raw[start:start + block_size]
        if mode == 'K':
            require(part[::-1][::-1] == part, 'bookkeeping inverse differs')
        direction = int(mode == 'D')
        coded = part[::-1] if direction else part
        payload = bz2.compress(coded, compresslevel=9)
        require(len(output) + FRAME.size + len(payload) <= MAX_ARCHIVE, 'archive output bound')
        output.extend(FRAME.pack(len(part), len(payload), direction, hashlib.sha256(part).digest()))
        output.extend(payload)
        rows.append(frame_report(part, coded, len(payload), direction))
    archive = bytes(output)
    return archive, dict(report(raw, archive, block_size, rows), requested_mode=mode)


def decode(archive, max_output=MAX_RAW):
    require(isinstance(archive, bytes) and HEADER.size <= len(archive) <= MAX_ARCHIVE,
            'archive input bound')
    magic, block_size, count, total = HEADER.unpack_from(archive)
    require(magic == MAGIC and 1 <= block_size <= MAX_BLOCK
            and type(max_output) is int and 0 <= total <= min(max_output, MAX_RAW)
            and count == (total + block_size - 1) // block_size, 'archive header bound')
    cursor, output, rows = HEADER.size, bytearray(), []
    for index in range(count):
        require(cursor + FRAME.size <= len(archive), 'truncated frame header')
        raw_size, payload_size, direction, digest = FRAME.unpack_from(archive, cursor)
        cursor += FRAME.size
        require(raw_size == min(block_size, total - index * block_size) and direction in (0, 1)
                and 0 < payload_size <= MAX_ARCHIVE and cursor + payload_size <= len(archive),
                'frame identity or payload bound')
        payload = archive[cursor:cursor + payload_size]
        cursor += payload_size
        inflater = bz2.BZ2Decompressor()
        try:
            coded = inflater.decompress(payload, max_length=raw_size + 1)
        except (OSError, EOFError) as error:
            raise CodecError('invalid BZip2 stream') from error
        require(len(coded) == raw_size and inflater.eof and not inflater.unused_data,
                'BZip2 output length, termination or trailing bytes differ')
        raw = coded[::-1] if direction else coded
        require(hashlib.sha256(raw).digest() == digest, 'raw checksum differs')
        output.extend(raw)
        rows.append(frame_report(raw, coded, payload_size, direction))
    require(cursor == len(archive) and len(output) == total, 'archive termination differs')
    raw = bytes(output)
    return raw, report(raw, archive, block_size, rows)


def new_file(path, data):
    """Refuse replacement and remove only this invocation's incomplete file."""
    with Path(path).open('xb') as target:
        try:
            target.write(data)
            target.flush()
            os.fsync(target.fileno())
        except BaseException:
            Path(path).unlink()
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('encode', 'decode'))
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--mode', choices=('P', 'K', 'D'), default='D')
    parser.add_argument('--block-size', type=int, default=MAX_BLOCK)
    args = parser.parse_args()
    start, cpu = time.monotonic(), time.process_time()
    bound = MAX_RAW if args.operation == 'encode' else MAX_ARCHIVE
    with args.input.open('rb') as source:
        data = source.read(bound + 1)
    require(len(data) <= bound, 'file input bound')
    output, result = encode(data, args.mode, args.block_size) if args.operation == 'encode' else decode(data)
    new_file(args.output, output)
    print(json.dumps(dict(result=result, cpu_seconds=time.process_time() - cpu,
                          elapsed_seconds=time.monotonic() - start,
                          peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                          complete_package_bytes=None, full_corpus_score_bytes=None), sort_keys=True))


if __name__ == '__main__':
    main()
