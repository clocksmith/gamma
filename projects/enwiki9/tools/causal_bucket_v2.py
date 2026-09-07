#!/usr/bin/env python3
"""Stable predecessor-byte permutation with histogram-derived FIFO boundaries."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sys
import time
import zlib

spec = importlib.util.spec_from_file_location("_bucket_base", Path(__file__).with_name("dualstream_grammar_v1.py"))
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)
require, CodecError = base.require, base.CodecError
HEADER, FRAME = base.HEADER, base.FRAME
MAX_FRAME, MAX_RAW, MAX_ARCHIVE = base.MAX_FRAME, base.MAX_RAW, base.MAX_ARCHIVE
MAGIC, PLAIN_MAGIC = b"D2BUKT01", b"D2GRAM02"
TRANSFORM_SPEC = dict(initial_predecessor=0, bucket_order="ascending-byte", within_bucket="stable-FIFO",
                      stored_endpoint="one-final-raw-byte", counts="histogram+initial-final",
                      deflate_level=9, admission="strict-complete-frame-saving", max_frame_bytes=65536)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def transform(raw):
    require(isinstance(raw, bytes) and len(raw) <= MAX_FRAME, "transform input bound")
    if not raw:
        return b""
    buckets, previous = [bytearray() for _ in range(256)], 0
    for value in raw:
        buckets[previous].append(value)
        previous = value
    return bytes([previous]) + b"".join(buckets)


def counts(payload):
    require(isinstance(payload, bytes) and 2 <= len(payload) <= MAX_FRAME + 1, "bucket payload bound")
    sizes = [0] * 256
    for value in payload[1:]:
        sizes[value] += 1
    sizes[0] += 1
    sizes[payload[0]] -= 1
    require(min(sizes) >= 0 and sum(sizes) == len(payload) - 1, "invalid bucket counts")
    return sizes


def inverse(payload):
    if payload == b"":
        return b""
    sizes = counts(payload)
    ends, cursors, offset = [], [], 1
    for size in sizes:
        cursors.append(offset)
        offset += size
        ends.append(offset)
    output, previous = bytearray(), 0
    for _ in range(len(payload) - 1):
        require(cursors[previous] < ends[previous], "bucket exhausted before output ended")
        value = payload[cursors[previous]]
        cursors[previous] += 1
        output.append(value)
        previous = value
    require(cursors == ends and previous == payload[0], "unconsumed buckets or final byte differs")
    return bytes(output)


def frame(raw, payload, selected):
    compressed = zlib.compress(payload, 9)
    encoded = FRAME.pack(len(raw), 5 if selected else 0, 0, 0, 0, len(compressed), 0,
                         hashlib.sha256(raw).digest()) + compressed
    report = dict(raw_bytes=len(raw), raw_sha256=sha(raw), output_sha256=sha(raw),
                  mode="bucket" if selected else "plain", complete_frame_bytes=len(encoded),
                  costs=dict(deflate_payload=len(compressed), framing=FRAME.size),
                  transmitted_payload_sha256=sha(payload))
    return encoded, report


def report(raw, archive, frame_size, frames):
    return dict(raw_bytes=len(raw), raw_sha256=sha(raw), complete_archive_bytes=len(archive),
                archive_sha256=sha(archive), frame_size=frame_size, backend="zlib9",
                zlib_version=zlib.ZLIB_RUNTIME_VERSION, frames=frames,
                costs=dict(deflate_payload=sum(f["costs"]["deflate_payload"] for f in frames),
                           framing=HEADER.size + FRAME.size * len(frames)),
                complete_package_bytes=None, full_corpus_score_bytes=None)


def encode(raw, mode="D", frame_size=MAX_FRAME):
    require(isinstance(raw, bytes) and len(raw) <= MAX_RAW and mode in ("K", "D")
            and 1 <= frame_size <= MAX_FRAME, "encoder input bound")
    count = (len(raw) + frame_size - 1) // frame_size
    require(HEADER.size + count * FRAME.size <= MAX_ARCHIVE, "archive framing bound")
    archive_bytes = HEADER.size
    frames, bodies = [], []
    for start in range(0, len(raw), frame_size):
        part = raw[start:start + frame_size]
        transformed = transform(part)
        require(inverse(transformed) == part, "bookkeeping inverse differs")
        plain, p = frame(part, part, False)
        bucket, b = frame(part, transformed, True)
        selected = mode == "D" and len(bucket) < len(plain)
        body, row = (bucket, b) if selected else (plain, p)
        row["comparison"] = dict(plain_bytes=len(plain), bucket_bytes=len(bucket), delta=len(plain) - len(bucket),
                                 selected=selected, transform_sha256=sha(transformed),
                                 counts_sha256=sha(b"".join(x.to_bytes(4, "little") for x in counts(transformed))))
        archive_bytes += len(body)
        require(archive_bytes <= MAX_ARCHIVE, "archive output bound")
        frames.append(row)
        bodies.append(body)
    magic = MAGIC if any(f["mode"] == "bucket" for f in frames) else PLAIN_MAGIC
    archive = HEADER.pack(magic, frame_size, len(frames), len(raw)) + b"".join(bodies)
    return archive, dict(report(raw, archive, frame_size, frames), mode=mode)


def decode(archive, max_output=MAX_RAW):
    require(isinstance(archive, bytes) and len(archive) <= MAX_ARCHIVE, "archive input bound")
    reader = base.Reader(archive)
    magic, frame_size, count, total = HEADER.unpack(reader.take(HEADER.size))
    require(magic in (MAGIC, PLAIN_MAGIC) and 1 <= frame_size <= MAX_FRAME
            and total <= min(max_output, MAX_RAW), "archive header bound")
    require(count == (total + frame_size - 1) // frame_size, "frame count differs")
    output, frames = bytearray(), []
    for i in range(count):
        raw_size, mode, *fields = FRAME.unpack(reader.take(FRAME.size))
        lengths, raw_hash = fields[:5], fields[5]
        require(raw_size == min(frame_size, total - i * frame_size) and mode in (0, 5)
                and (mode == 0 or magic == MAGIC), "frame identity differs")
        require(all(lengths[j] == 0 for j in (0, 1, 2, 4)) and lengths[3] <= 2 * base.MAX_SECTION,
                "invalid frame sections")
        payload = base.inflate(reader.take(lengths[3]))
        require(len(payload) == raw_size + (mode == 5), "payload size differs")
        raw = inverse(payload) if mode == 5 else payload
        require(len(raw) == raw_size and hashlib.sha256(raw).digest() == raw_hash, "raw checksum differs")
        frames.append(dict(raw_bytes=len(raw), raw_sha256=sha(raw), output_sha256=sha(raw),
                           mode="bucket" if mode == 5 else "plain", complete_frame_bytes=FRAME.size + lengths[3],
                           costs=dict(deflate_payload=lengths[3], framing=FRAME.size),
                           transmitted_payload_sha256=sha(payload)))
        output.extend(raw)
    reader.end()
    require(magic == (MAGIC if any(f["mode"] == "bucket" for f in frames) else PLAIN_MAGIC), "noncanonical archive identity")
    raw = bytes(output)
    return raw, report(raw, archive, frame_size, frames)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("encode", "decode"))
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mode", choices=("K", "D"), default="D")
    parser.add_argument("--frame-size", type=int, default=MAX_FRAME)
    args = parser.parse_args()
    start, cpu = time.monotonic(), time.process_time()
    limit = MAX_RAW if args.operation == "encode" else MAX_ARCHIVE
    with args.input.open("rb") as f:
        data = f.read(limit + 1)
    require(len(data) <= limit, "file input bound")
    output, result = encode(data, args.mode, args.frame_size) if args.operation == "encode" else decode(data)
    base.new_file(args.output, lambda f: f.write(output))
    print(json.dumps(dict(result=result, cpu_seconds=time.process_time() - cpu, elapsed_seconds=time.monotonic() - start,
                          peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                          complete_package_bytes=None, full_corpus_score_bytes=None), sort_keys=True))


if __name__ == "__main__":
    main()
