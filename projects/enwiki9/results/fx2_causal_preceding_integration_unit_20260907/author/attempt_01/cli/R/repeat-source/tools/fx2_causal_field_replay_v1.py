#!/usr/bin/env python3
"""Bounded conditional-field replay using explicitly supplied parent Q16 values.

This is a predictive-value diagnostic, not a standalone FX2 decoder. The parent
probability stream is an external decoding dependency and receives no package or
prize credit. Native framing and finite arithmetic are retained exactly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import struct
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from causal_field_wrt_adapter_v1 import Adapter
from causal_field_parent_coder_v1 import Encoder, Decoder, ParentMixture
from wrt_exact import read_dictionary_words

MAX_RAW = 250000
MAX_MODELED = 1000000
MAX_ARCHIVE = 2 * 1024 * 1024
PREFIX_BYTES = 46
ARMS = "PKTRS"
RECORD = struct.Struct("<7I")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def framing(prefix, raw_bytes, modeled_bytes):
    require(type(raw_bytes) is int and 0 <= raw_bytes <= MAX_RAW, "raw work bound differs")
    require(type(modeled_bytes) is int and 1 <= modeled_bytes <= MAX_MODELED, "modeled work bound differs")
    require(len(prefix) == PREFIX_BYTES and prefix[:5] == b"GFV1\x07", "native literal framing differs")
    require(int.from_bytes(prefix[5:9], "big") == raw_bytes, "framed raw length differs")
    require(int.from_bytes(prefix[9:14], "big") == (1 << 39) + modeled_bytes,
            "framed modeled length or trained-map flag differs")
    allowed = {value for value in range(256) if prefix[14 + value // 8] & (1 << (value % 8))}
    require(bool(allowed), "empty native vocabulary")
    return allowed


def project_trace(trace, modeled, parent_archive, raw_bytes):
    """Encoder-side audit; only its returned Q16 bytes may reach the decoder."""
    require(1 <= len(modeled) <= MAX_MODELED and len(trace) == len(modeled) * 8 * RECORD.size,
            "native trace record count differs")
    prefix = parent_archive[:PREFIX_BYTES]
    allowed = framing(prefix, raw_bytes, len(modeled))
    require(len(parent_archive) <= MAX_ARCHIVE and all(value in allowed for value in modeled),
            "native archive or vocabulary bound differs")
    coder = Encoder(max_bits=len(modeled) * 8, max_payload_bytes=MAX_ARCHIVE)
    probabilities = bytearray()
    for index, row in enumerate(RECORD.iter_unpack(trace)):
        fp, q, low, high, after_low, after_high, bit = row
        p = struct.unpack("<f", struct.pack("<I", fp))[0]
        require(math.isfinite(p) and 0 <= p <= 1 and 1 <= q <= 65535,
                "invalid native probability at bit " + str(index))
        require(bit == ((modeled[index // 8] >> (7 - index % 8)) & 1),
                "native trace truth differs at bit " + str(index))
        require((low, high) == (coder.low, coder.high), "native pre-interval differs at bit " + str(index))
        coder.encode(bit, q)
        require((after_low, after_high) == (coder.low, coder.high),
                "native post-interval differs at bit " + str(index))
        probabilities.extend(struct.pack("<H", q))
    payload = coder.finish()
    require(prefix + payload == parent_archive, "native parent payload replay differs")
    return bytes(probabilities), {"records": len(modeled) * 8, "record_bytes": RECORD.size,
        "q16_bytes": len(probabilities), "q16_sha256": sha(probabilities),
        "parent_payload_bytes": len(payload), "parent_archive_bytes": len(parent_archive),
        "parent_archive_sha256": sha(parent_archive), "native_intervals_and_payload_exact": True,
        "decoder_receives_truth_trace": False, "parent_probability_dependency": "retained Q16 stream"}


def replay(operation, body, q16, prefix, words, arm, raw_bytes, raw_sha256):
    require(operation in ("encode", "decode", "repeat") and arm in ARMS and len(arm) == 1,
            "invalid replay operation or arm")
    require(len(q16) % 16 == 0 and 16 <= len(q16) <= MAX_MODELED * 16, "Q16 stream length differs")
    count = len(q16) // 2
    modeled_bytes = count // 8
    allowed = framing(prefix, raw_bytes, modeled_bytes)
    require(isinstance(raw_sha256, str) and len(raw_sha256) == 64
            and all(c in "0123456789abcdef" for c in raw_sha256), "raw digest is not canonical")
    if operation == "decode":
        require(PREFIX_BYTES < len(body) <= MAX_ARCHIVE and body[:PREFIX_BYTES] == prefix,
                "archive framing differs")
        payload = body[PREFIX_BYTES:]
        coder = Decoder(payload, max_bits=count, expected_payload_bytes=len(payload), payload_sha256=sha(payload))
        canonical_encoder = Encoder(max_bits=count, max_payload_bytes=MAX_ARCHIVE)
    else:
        require(len(body) == modeled_bytes and all(value in allowed for value in body),
                "modeled population length or vocabulary differs")
        coder = Encoder(max_bits=count, max_payload_bytes=MAX_ARCHIVE)
        canonical_encoder = None
    adapter = Adapter(words, arm=arm, raw_limit=raw_bytes)
    mixture = ParentMixture(max_bits=count)
    activation = None
    raw = bytearray()
    modeled = bytearray()
    probabilities = hashlib.sha256(b"field-wrt-probabilities-v1\0")
    synchronization = hashlib.sha256(b"field-wrt-synchronization-v1\0").digest()
    synchronization_rows = bytearray()
    changed = active_bits = 0
    for index, (parent_q,) in enumerate(struct.iter_unpack("<H", q16)):
        require(1 <= parent_q <= 65535, "invalid Q16 at bit " + str(index))
        if adapter.activation_id != activation:
            mixture.reset(adapter.donor if arm in "TRS" else None)
            activation = adapter.activation_id
        q = mixture.predict(parent_q)
        changed += q != parent_q
        active_bits += bool(adapter.donor) and arm in "TRS"
        probabilities.update(struct.pack("<H", q))
        if operation == "decode":
            bit = coder.decode(q)
            canonical_encoder.encode(bit, q)
            require((coder.low, coder.high) == (canonical_encoder.low, canonical_encoder.high),
                    "independent interval differs at bit " + str(index))
        else:
            bit = (body[index // 8] >> (7 - index % 8)) & 1
            coder.encode(bit, q)
        mixture.observe(bit)
        if index % 8 == 0:
            modeled.append(0)
        modeled[-1] = (modeled[-1] << 1) | bit
        if index % 8 == 7:
            require(modeled[-1] in allowed, "decoded symbol exceeds native vocabulary")
            emission = adapter.feed(modeled[-1])
            require(len(raw) + len(emission) <= raw_bytes, "decoded raw bound exceeded")
            raw.extend(emission)
            state = (bytes.fromhex(adapter.state_digest()) + bytes.fromhex(mixture.state_digest())
                     + struct.pack("<II", coder.low, coder.high))
            synchronization = hashlib.sha256(synchronization + state).digest()
            synchronization_rows.extend(synchronization)
    adapter_stats = adapter.finish()
    require(len(raw) == raw_bytes and sha(raw) == raw_sha256, "exact raw inverse differs")
    if operation == "decode":
        require(canonical_encoder.finish() == payload, "noncanonical, truncated or trailing arithmetic payload")
        archive = body
        output = bytes(raw)
    else:
        archive = prefix + coder.finish()
        require(len(archive) <= MAX_ARCHIVE, "archive work bound exceeded")
        output = archive
    report = {"arm": arm, "raw_bytes": len(raw), "raw_sha256": sha(raw),
        "modeled_bytes": len(modeled), "modeled_sha256": sha(modeled),
        "archive_bytes": len(archive), "archive_sha256": sha(archive),
        "prefix_bytes": PREFIX_BYTES, "payload_bytes": len(archive) - PREFIX_BYTES,
        "probability_digest": probabilities.hexdigest(), "synchronization_digest": synchronization.hex(),
        "synchronization_rows": modeled_bytes, "adapter_state_digest": adapter.state_digest(),
        "mixture_state_digest": mixture.state_digest(), "changed_probability_bits": changed,
        "donor_present_bits": active_bits, "adapter": adapter_stats,
        "external_parent_q16_bytes": len(q16), "external_parent_q16_sha256": sha(q16),
        "exact_raw_inverse": True, "standalone_decoder": False, "objective_credit_bytes": 0,
        "complete_package_bytes": None, "full_corpus_score_bytes": None}
    return output, bytes(synchronization_rows), report


def read_bounded(path, cap):
    with Path(path).open("rb") as handle:
        before = os.fstat(handle.fileno())
        require(before.st_size <= cap, "input exceeds bound: " + str(path))
        data = handle.read(cap + 1)
        after = os.fstat(handle.fileno())
    require(len(data) <= cap and (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), "input changed while reading")
    return data


def publish(path, data):
    path = Path(path)
    require(not path.exists() and not path.is_symlink(), "output already exists")
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        os.unlink(temporary)


def restrict(resource_id, cap):
    soft, hard = resource.getrlimit(resource_id)
    bound = min([cap] + [value for value in (soft, hard) if value != resource.RLIM_INFINITY])
    resource.setrlimit(resource_id, (bound, bound))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("encode", "decode", "repeat"))
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--sync", required=True, type=Path)
    parser.add_argument("--q16", required=True, type=Path)
    parser.add_argument("--dictionary", required=True, type=Path)
    parser.add_argument("--arm", required=True, choices=tuple(ARMS))
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--raw-bytes", required=True, type=int)
    parser.add_argument("--raw-sha256", required=True)
    args = parser.parse_args(argv)
    # These are child limits; the canonical runner also owns aggregate guards.
    restrict(resource.RLIMIT_AS, 512 * 1024 * 1024)
    restrict(resource.RLIMIT_CPU, 120)
    restrict(resource.RLIMIT_FSIZE, 32 * 1024 * 1024)
    require(args.output != args.sync and not args.output.exists() and not args.sync.exists(), "output collision")
    source = read_bounded(args.input, MAX_ARCHIVE)
    q16 = read_bounded(args.q16, MAX_MODELED * 16)
    dictionary = read_bounded(args.dictionary, 2 * 1024 * 1024)
    # read_dictionary_words is the unchanged reference; authenticate its read.
    words = read_dictionary_words(args.dictionary)
    require(read_bounded(args.dictionary, 2 * 1024 * 1024) == dictionary, "dictionary changed")
    started, cpu = time.monotonic(), time.process_time()
    output, sync, result = replay(args.operation, source, q16, bytes.fromhex(args.prefix),
                                  words, args.arm, args.raw_bytes, args.raw_sha256)
    publish(args.output, output)
    publish(args.sync, sync)
    result.update(operation=args.operation, cpu_seconds=time.process_time() - cpu,
                  wall_seconds=time.monotonic() - started,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  pid=os.getpid(), cpu_affinity=sorted(os.sched_getaffinity(0)),
                  source_sha256=sha(Path(__file__).read_bytes()),
                  dictionary_sha256=sha(dictionary), synchronization_file_sha256=sha(sync))
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
