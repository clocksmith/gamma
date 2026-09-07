#!/usr/bin/env python3
"""Synthetic prefix-causal flat-template dependency predictor and exact codec.

The uniform parent has no competitive compression inheritance. A donor is chosen
only after a later field's '=' has been decoded. New associations are committed
only after the entire bounded, flat invocation closes. Bytes are never changed.
"""
from __future__ import annotations

import argparse
from collections import OrderedDict
import hashlib
import json
import os
from pathlib import Path
import resource
import struct
import sys
import tempfile
import time

TOOLS = Path(__file__).resolve().parent
SOURCE_PINS = {"streaming_retrieval_codec.py": "2f755fb86fe9b7ffa5bc3735a0f1fdeb6759fc475dd50cb03c515f13d8023921",
               "fx2_shadow_residual_coder.py": "c0fdf0bed0502cc874103bdde0af8698cc8c660d4a977250a4de1fedb44eec6f"}
for _name, _digest in SOURCE_PINS.items():
    if hashlib.sha256((TOOLS / _name).read_bytes()).hexdigest() != _digest:
        raise ValueError("arithmetic primitive source changed: " + _name)
sys.path.insert(0, str(TOOLS))
from streaming_retrieval_codec import ArithmeticEncoder, ArithmeticDecoder

MAX_RAW = 8192
MAX_ARCHIVE = 262144
MAX_STATE = 262144
MAX_ENTRIES = 128
MAX_FIELDS = 8
MAX_VALUE = 64
MAX_NAME = 32
MAX_INVOCATION = 2048
TOTAL = 65536
ARMS = "PKTRS"
HEADER = struct.Struct("<4scII32s32s")
MAGIC = b"CFD1"
LAST_REPORT = {}


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).digest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def bounded_int(value, low, high):
    require(type(value) is int and low <= value <= high, "invalid checkpoint integer")
    return value


def unhex(value, maximum):
    require(isinstance(value, str) and len(value) <= maximum * 2, "invalid checkpoint byte field")
    raw = bytes.fromhex(value)
    require(raw.hex() == value, "noncanonical checkpoint byte field")
    return raw


class PrefixParser:
    """The only input is the next already reconstructed byte; no record lookahead."""
    def __init__(self, owner):
        self.owner = owner
        self.mode = "outside"
        self.open_pending = False
        self.depth = 0
        self.brace = 0
        self.count = 0
        self.name = bytearray()
        self.key = bytearray()
        self.value = bytearray()
        self.fields = []

    def reset(self):
        self.__init__(self.owner)
        self.owner.clear_donor()

    def invalidate(self):
        self.mode = "invalid"
        self.name.clear()
        self.key.clear()
        self.value.clear()
        self.fields.clear()
        self.owner.clear_donor()

    def finish_field(self):
        if not self.key or len(self.fields) >= MAX_FIELDS:
            self.invalidate()
            return
        self.fields.append((bytes(self.key), bytes(self.value)))
        self.key.clear()
        self.value.clear()
        self.owner.clear_donor()

    def feed(self, byte):
        if self.mode == "outside":
            if self.open_pending and byte == 123:
                self.mode, self.depth, self.count, self.open_pending = "name", 1, 2, False
            else:
                self.open_pending = byte == 123
            return
        self.count = min(self.count + 1, MAX_INVOCATION + 1)
        if self.brace == byte and byte in (123, 125):
            self.depth += 1 if byte == 123 else -1
            self.brace = 0
        else:
            self.brace = byte if byte in (123, 125) else 0
        if self.depth > 1 or self.count > MAX_INVOCATION:
            self.invalidate()
        if self.mode != "invalid":
            if byte == 123:
                self.invalidate()
            elif self.mode == "name":
                if byte == 124 and self.name:
                    self.mode = "key"
                elif byte == 125 and self.name:
                    self.mode = "close"
                elif byte in (124, 125) or len(self.name) == MAX_NAME:
                    self.invalidate()
                else:
                    self.name.append(byte)
            elif self.mode == "key":
                if byte == 61 and self.key and not any(key == self.key for key, _ in self.fields):
                    self.mode = "value"
                    self.owner.start_value(bytes(self.name), self.fields, bytes(self.key))
                elif byte in (61, 124, 125) or len(self.key) == MAX_NAME or len(self.fields) == MAX_FIELDS:
                    self.invalidate()
                else:
                    self.key.append(byte)
            elif self.mode == "value":
                if byte in (124, 125):
                    self.finish_field()
                    if self.mode != "invalid":
                        self.mode = "key" if byte == 124 else "close"
                elif len(self.value) == MAX_VALUE:
                    self.invalidate()
                else:
                    self.value.append(byte)
            elif self.mode == "close" and byte != 125:
                self.invalidate()
        if self.depth == 0:
            if self.mode == "close":
                self.owner.commit(bytes(self.name), self.fields)
            else:
                self.owner.rejected_invocations += 1
            self.reset()

    def export(self):
        return {"mode": self.mode, "open_pending": self.open_pending, "depth": self.depth,
                "brace": self.brace, "count": self.count, "name": self.name.hex(),
                "key": self.key.hex(), "value": self.value.hex(),
                "fields": [[key.hex(), value.hex()] for key, value in self.fields]}

    def restore(self, row):
        require(set(row) == set(self.export()) and row["mode"] in ("outside", "name", "key", "value", "close", "invalid"), "invalid parser checkpoint")
        self.mode = row["mode"]
        require(type(row["open_pending"]) is bool, "invalid pending opener")
        self.open_pending = row["open_pending"]
        self.depth = bounded_int(row["depth"], 0, MAX_RAW // 2)
        self.brace = bounded_int(row["brace"], 0, 125)
        require(self.brace in (0, 123, 125), "invalid brace state")
        self.count = bounded_int(row["count"], 0, MAX_INVOCATION + 1)
        self.name = bytearray(unhex(row["name"], MAX_NAME))
        self.key = bytearray(unhex(row["key"], MAX_NAME))
        self.value = bytearray(unhex(row["value"], MAX_VALUE))
        require(isinstance(row["fields"], list) and len(row["fields"]) <= MAX_FIELDS, "field bound exceeded")
        self.fields = [(unhex(key, MAX_NAME), unhex(value, MAX_VALUE)) for key, value in row["fields"]]
        require(all(key for key, _ in self.fields) and len({key for key, _ in self.fields}) == len(self.fields), "invalid completed fields")
        require((self.mode == "outside") == (self.depth == 0), "parser depth disagrees with mode")


class Predictor:
    def __init__(self, arm="T"):
        require(arm in ARMS and len(arm) == 1, "unknown arm")
        self.arm = arm
        self.parser = PrefixParser(self)
        self.table = OrderedDict()
        self.serial = 0
        self.table_hash = digest(canonical([])).hex()
        self.bits = self.partial = self.partial_bits = 0
        self.pending = None
        self.probability_hash = digest(b"CFD-probabilities-v1")
        self.truth_hash = digest(b"CFD-truths-v1")
        self.donor = None
        self.donor_bit = 0
        self.alive = False
        self.selected_values = self.specialist_bits = 0
        self.completed_invocations = self.rejected_invocations = self.evictions = 0

    def clear_donor(self):
        self.donor, self.donor_bit, self.alive = None, 0, False

    def start_value(self, template, fields, key):
        self.clear_donor()
        if not fields:
            return
        first_key, first_value = fields[0]
        lookup = (template, first_key, first_value, key)
        donor = self.table.get(lookup)
        if self.arm == "R":
            available = [value for ident, value in self.table.items() if ident[0] == template and ident[3] == key]
            donor = max(available, key=lambda value: value[1]) if available else None
        elif self.arm == "S":
            keys = [ident for ident in self.table if (ident[0], ident[1], ident[3]) == (template, first_key, key)]
            donor = self.table[keys[(keys.index(lookup) + 1) % len(keys)]] if lookup in keys and len(keys) >= 2 else None
        if donor is not None:
            self.donor, self.alive = donor[0], True
            self.selected_values += 1

    def commit(self, template, fields):
        self.completed_invocations += 1
        if len(fields) < 2:
            return
        first_key, first_value = fields[0]
        for key, value in fields[1:]:
            ident = (template, first_key, first_value, key)
            if ident not in self.table and len(self.table) == MAX_ENTRIES:
                self.table.popitem(last=False)
                self.evictions += 1
            self.serial += 1
            self.table[ident] = (value, self.serial)
        self.table_hash = digest(canonical(self.table_rows())).hex()

    def predict(self):
        require(self.bits < MAX_RAW * 8, "raw work bound exceeded")
        if self.pending is None:
            p1 = TOTAL // 2
            if self.arm in "TRS" and self.donor is not None and self.alive and self.donor_bit < len(self.donor) * 8:
                bit = (self.donor[self.donor_bit // 8] >> (7 - self.donor_bit % 8)) & 1
                # Exact half-prior odds after k matching deterministic donor bits.
                odds = 1 << self.donor_bit
                p1 = max(1, min(TOTAL - 1, TOTAL * (1 + 2 * odds * bit) // (2 * (1 + odds))))
            self.pending = p1
        return self.pending

    def observe(self, bit):
        require(type(bit) is int and bit in (0, 1) and self.pending is not None, "predict must precede decoded truth")
        require(self.bits < MAX_RAW * 8, "raw work bound exceeded")
        self.probability_hash = digest(self.probability_hash + struct.pack("<H", self.pending))
        self.truth_hash = digest(self.truth_hash + bytes([bit]))
        self.pending = None
        if self.donor is not None and self.donor_bit < len(self.donor) * 8:
            predicted = (self.donor[self.donor_bit // 8] >> (7 - self.donor_bit % 8)) & 1
            if self.alive:
                if self.arm in "TRS":
                    self.specialist_bits += 1
                self.alive = bit == predicted
            self.donor_bit += 1
        self.partial = (self.partial << 1) | bit
        self.partial_bits += 1
        self.bits += 1
        if self.partial_bits == 8:
            if self.arm != "P":
                self.parser.feed(self.partial)
            self.partial = self.partial_bits = 0

    def table_rows(self):
        return [[*[part.hex() for part in key], value.hex(), serial] for key, (value, serial) in self.table.items()]

    def snapshot(self, *, include_table=True):
        row = {"version": 1, "arm": self.arm, "bits": self.bits, "partial": self.partial,
               "partial_bits": self.partial_bits, "pending": self.pending,
               "probability_hash": self.probability_hash.hex(), "truth_hash": self.truth_hash.hex(),
               "parser": self.parser.export(), "table_hash": self.table_hash, "serial": self.serial,
               "donor": None if self.donor is None else self.donor.hex(), "donor_bit": self.donor_bit,
               "alive": self.alive, "selected_values": self.selected_values, "specialist_bits": self.specialist_bits,
               "completed_invocations": self.completed_invocations, "rejected_invocations": self.rejected_invocations,
               "evictions": self.evictions}
        if include_table:
            row["table"] = self.table_rows()
        return row

    def state_digest(self):
        return digest(canonical(self.snapshot(include_table=False))).hex()

    def serialize(self):
        payload = canonical(self.snapshot())
        require(len(payload) <= MAX_STATE - 41, "checkpoint size bound exceeded")
        return b"CFDS1" + struct.pack("<I", len(payload)) + digest(payload) + payload

    @classmethod
    def restore(cls, blob):
        require(isinstance(blob, bytes) and 41 <= len(blob) <= MAX_STATE and blob[:5] == b"CFDS1", "invalid checkpoint framing")
        payload = blob[41:]
        require(struct.unpack("<I", blob[5:9])[0] == len(payload) and blob[9:41] == digest(payload), "checkpoint length or hash differs")
        row = json.loads(payload)
        model = cls(row["arm"])
        require(set(row) == set(model.snapshot()) and row["version"] == 1, "checkpoint fields differ")
        for key, maximum in (("bits", MAX_RAW * 8), ("partial_bits", 7), ("partial", 127),
                ("serial", MAX_RAW * MAX_FIELDS), ("selected_values", MAX_RAW), ("specialist_bits", MAX_RAW * 8),
                ("completed_invocations", MAX_RAW), ("rejected_invocations", MAX_RAW), ("evictions", MAX_RAW * MAX_FIELDS),
                ("donor_bit", MAX_VALUE * 8)):
            setattr(model, key, bounded_int(row[key], 0, maximum))
        require(model.bits % 8 == model.partial_bits and model.partial < 1 << model.partial_bits, "partial byte state differs")
        model.pending = None if row["pending"] is None else bounded_int(row["pending"], 1, TOTAL - 1)
        for key in ("probability_hash", "truth_hash"):
            value = unhex(row[key], 32)
            require(len(value) == 32, "rolling hash length differs")
            setattr(model, key, value)
        model.donor = None if row["donor"] is None else unhex(row["donor"], MAX_VALUE)
        require(type(row["alive"]) is bool, "invalid posterior state")
        model.alive = row["alive"]
        require(model.donor_bit <= (len(model.donor) * 8 if model.donor is not None else 0)
                and (model.donor is not None or not model.alive), "donor position differs")
        require(isinstance(row["table"], list) and len(row["table"]) <= MAX_ENTRIES, "dictionary bound exceeded")
        for entry in row["table"]:
            require(isinstance(entry, list) and len(entry) == 6, "invalid association")
            ident = tuple(unhex(entry[i], MAX_VALUE if i == 2 else MAX_NAME) for i in range(4))
            value, serial = unhex(entry[4], MAX_VALUE), bounded_int(entry[5], 1, model.serial)
            require(all(ident[i] for i in (0, 1, 3)) and ident not in model.table, "invalid association key")
            model.table[ident] = (value, serial)
        model.table_hash = digest(canonical(model.table_rows())).hex()
        require(model.table_hash == row["table_hash"], "dictionary digest differs")
        serials = [value[1] for value in model.table.values()]
        require(len(set(serials)) == len(serials) and (max(serials) if serials else 0) == model.serial, "association update order differs")
        model.parser.restore(row["parser"])
        if model.pending is not None:
            pending, model.pending = model.pending, None
            require(model.bits < MAX_RAW * 8 and model.predict() == pending, "pending probability disagrees with predictor")
        require(model.serialize() == blob, "noncanonical checkpoint state")
        return model


def synchronize(chain, model, coder):
    return digest(chain + bytes.fromhex(model.state_digest()) + struct.pack("<II", coder.low, coder.high))


def result(raw, archive, payload, model, sync):
    return {"schema": "gamma.enwiki9.causal-field-codec-result.v1", "arm": model.arm,
            "raw_bytes": len(raw), "raw_sha256": digest(raw).hex(), "archive_sha256": digest(archive).hex(),
            "complete_archive_bytes": len(archive), "header_bytes": HEADER.size, "payload_bytes": len(payload),
            "probability_digest": model.probability_hash.hex(), "state_digest": model.state_digest(),
            "synchronization_digest": sync.hex(), "dictionary_digest": model.table_hash,
            "dictionary_entries": len(model.table), "completed_invocations": model.completed_invocations,
            "rejected_invocations": model.rejected_invocations, "selected_values": model.selected_values,
            "specialist_bits": model.specialist_bits, "evictions": model.evictions,
            "state_bytes": len(model.serialize()), "complete_package_bytes": None,
            "qualification_authority": False, "objective_credit_bytes": 0, "synthetic_only": True}


def encode(raw, arm="T"):
    require(isinstance(raw, bytes) and len(raw) <= MAX_RAW, "synthetic raw bound exceeded")
    model, coder = Predictor(arm), ArithmeticEncoder()
    sync = digest(b"CFD-state-and-interval-v1")
    for byte in raw:
        for shift in range(7, -1, -1):
            probability = model.predict()
            bit = (byte >> shift) & 1
            coder.encode(bit, probability)
            model.observe(bit)
        sync = synchronize(sync, model, coder)
    payload = coder.finish()
    stored_arm = "P" if arm in "PK" else arm
    archive = HEADER.pack(MAGIC, stored_arm.encode(), len(raw), len(payload), digest(raw), digest(payload)) + payload
    require(len(archive) <= MAX_ARCHIVE, "archive bound exceeded")
    return archive, result(raw, archive, payload, model, sync)


def decode(archive, arm=None):
    require(isinstance(archive, bytes) and HEADER.size <= len(archive) <= MAX_ARCHIVE, "archive bound or framing differs")
    magic, stored, length, packed, raw_hash, payload_hash = HEADER.unpack(archive[:HEADER.size])
    require(magic == MAGIC and stored in (b"P", b"T", b"R", b"S") and length <= MAX_RAW, "unknown archive or raw bound")
    selected = stored.decode() if arm is None else arm
    require(selected in ARMS and len(selected) == 1 and (stored == b"P" if selected in "PK" else stored == selected.encode()), "archive arm differs")
    payload = archive[HEADER.size:]
    require(len(payload) == packed and digest(payload) == payload_hash, "payload length or hash differs")
    model, coder, check = Predictor(selected), ArithmeticDecoder(payload), ArithmeticEncoder()
    sync = digest(b"CFD-state-and-interval-v1")
    raw = bytearray()
    for _ in range(length):
        byte = 0
        for _ in range(8):
            probability = model.predict()
            bit = coder.decode(probability)
            check.encode(bit, probability)
            model.observe(bit)
            byte = (byte << 1) | bit
        require((check.low, check.high) == (coder.low, coder.high), "arithmetic interval diverged")
        sync = synchronize(sync, model, coder)
        raw.append(byte)
    require(digest(raw) == raw_hash and check.finish() == payload, "raw checksum or canonical arithmetic termination differs")
    raw = bytes(raw)
    return raw, result(raw, archive, payload, model, sync)


def compress_arm(raw, arm):
    global LAST_REPORT
    archive, LAST_REPORT = encode(raw, arm)
    return archive


def decompress_arm(archive, arm):
    global LAST_REPORT
    raw, LAST_REPORT = decode(archive, arm)
    return raw


def stats():
    return dict(LAST_REPORT)


def publish(path, payload):
    path = Path(path)
    require(not path.exists(), "output already exists")
    fd, name = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def source_inventory():
    from enwiki9_python_source_closure import local_source_closure
    return [{"path": str(path.relative_to(TOOLS.parent)), "bytes": path.stat().st_size,
             "sha256": digest(path.read_bytes()).hex()} for path in local_source_closure([Path(__file__)])]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("encode", "decode", "repeat", "inventory"))
    parser.add_argument("input", nargs="?", type=Path)
    parser.add_argument("output", nargs="?", type=Path)
    parser.add_argument("--arm", choices=tuple(ARMS))
    args = parser.parse_args(argv)
    if args.operation == "inventory":
        print(json.dumps({"files": source_inventory(), "complete_package_bytes": None, "qualification_authority": False}))
        return 0
    require(args.input is not None and args.output is not None, "input and output are required")
    maximum = MAX_ARCHIVE if args.operation == "decode" else MAX_RAW
    require(args.input.stat().st_size <= maximum, "input exceeds synthetic bound")
    with args.input.open("rb") as stream:
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum, "input grew beyond bound")
    started, cpu = time.monotonic(), time.process_time()
    output, report = decode(raw, args.arm) if args.operation == "decode" else encode(raw, args.arm or "T")
    publish(args.output, output)
    print(json.dumps({"result": report, "cpu_seconds": time.process_time() - cpu,
                      "wall_seconds": time.monotonic() - started,
                      "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      "pid": os.getpid(), "cpu_affinity": sorted(os.sched_getaffinity(0)),
                      "python": sys.version, "executable": sys.executable,
                      "source_sha256": digest(Path(__file__).read_bytes()).hex()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
