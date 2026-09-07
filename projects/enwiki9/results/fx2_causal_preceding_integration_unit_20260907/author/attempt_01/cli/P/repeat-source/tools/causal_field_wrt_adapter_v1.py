#!/usr/bin/env python3
"""Incremental, event-aligned WRT frontend for the frozen causal field parser.

Input is modeled bytes (stored[10:]), starting with dictionary-transform flag 7.
The caller binds the dictionary and exact expected raw length. Donors contain
historical modeled bytes, never raw bytes reinterpreted as WRT. This module does
not open corpora, models, dictionaries or traces and performs no arithmetic coding.
"""
from __future__ import annotations

import ast
from collections import Counter, OrderedDict
import hashlib
import json
from pathlib import Path
import struct
import sys
from types import ModuleType

TOOLS = Path(__file__).resolve().parent
PINS = {"causal_field_dependency_v1.py": "f34a42054ba151219c67060cf3420e06fb1e1aff8ea9f01aa408e116b495ec0a",
        "wrt_exact.py": "ae08246ee8b4708904f78aa5f694111834d6420deece34957c61d6fea3a9797a"}
MAX_RAW = 250000
MAX_DONOR = 256
MAX_ENTRIES = 128
MAX_DICTIONARY_WORDS = 44880
MAX_DICTIONARY_BYTES = 16 * 1024**2


def require(value, message):
    if not value:
        raise ValueError(message)


def encoded_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def load_frozen(name, *, parser_only=False):
    path = TOOLS / name
    source = path.read_bytes()
    require(hashlib.sha256(source).hexdigest() == PINS[name], "frozen frontend source changed: " + name)
    tree = ast.parse(source, filename=str(path))
    if parser_only:
        constants = {"MAX_RAW", "MAX_FIELDS", "MAX_NAME", "MAX_VALUE", "MAX_INVOCATION"}
        definitions = {"PrefixParser", "require", "bounded_int", "unhex"}
        nodes = [node for node in tree.body if
                 isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in definitions or
                 isinstance(node, ast.Assign) and len(node.targets) == 1 and
                 isinstance(node.targets[0], ast.Name) and node.targets[0].id in constants]
        require(len(nodes) == len(constants) + len(definitions), "frozen parser definition selection differs")
        tree = ast.Module(body=nodes, type_ignores=[])
    module = ModuleType(__name__ + ".frozen_" + path.stem)
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(tree, str(path), "exec"), module.__dict__)
    return module


_parser_source = load_frozen("causal_field_dependency_v1.py", parser_only=True)
wrt = load_frozen("wrt_exact.py")


class FieldParser(_parser_source.PrefixParser):
    """Preserve frozen syntax decisions; add only completed-field span hooks."""
    def finish_field(self):
        self.owner.finish_field(bytes(self.key), bytes(self.value))
        super().finish_field()

    def invalidate(self):
        self.owner.discard_invocation_spans()
        super().invalidate()

    def reset(self):
        self.owner.discard_invocation_spans()
        super().reset()


class Adapter:
    def __init__(self, words, arm="T", raw_limit=MAX_RAW):
        require(type(raw_limit) is int and 0 <= raw_limit <= MAX_RAW, "expected raw length exceeds bound")
        require(isinstance(arm, str) and len(arm) == 1 and arm in "PKTRS", "unknown arm")
        require(isinstance(words, (tuple, list)) and len(words) <= MAX_DICTIONARY_WORDS, "dictionary count exceeds bound")
        require(all(isinstance(word, bytes) and 0 < len(word) <= MAX_RAW for word in words), "invalid dictionary word")
        require(sum(map(len, words)) <= MAX_DICTIONARY_BYTES, "dictionary byte bound exceeded")
        self.words, self.arm, self.raw_limit = tuple(words), arm, raw_limit
        dictionary_hash = hashlib.sha256(b"field-WRT-dictionary-v1\0")
        for word in self.words:
            dictionary_hash.update(struct.pack("<I", len(word)) + word)
        self.dictionary_digest = dictionary_hash.hexdigest()
        self.decoder = wrt.WrtDecoderState()
        self.parser = FieldParser(self)
        self.modeled_count = self.raw_count = 0
        self.modeled_limit = 4 * raw_limit + 4096
        self.modeled_hash, self.raw_hash = hashlib.sha256(), hashlib.sha256()
        self.pending = bytearray()
        self.event_start = 0
        self.event_entry = (False, False)
        self.event = None
        self.raw_index = 0
        self.flag_seen = self.finished = self.failed = False
        self.failure = None
        self.current_value = None
        self.completed_spans = {}
        self.table = OrderedDict()
        self.serial = 0
        self.table_digest = hashlib.sha256(encoded_json([])).hexdigest()
        self.donor = None
        self.activation_id = 0
        self.completed_invocations = self.rejected_invocations = 0
        self.unaligned_values = self.oversized_donors = self.incompatible_lookups = 0
        self.selected_values = self.evictions = 0
        self.event_counts = Counter()

    def wrt_state(self):
        return self.decoder.uppercase, self.decoder.capitalized

    def clear_donor(self):
        self.donor = None
        self.activation_id += 1

    def discard_invocation_spans(self):
        self.current_value = None
        self.completed_spans.clear()

    def start_value(self, template, fields, key):
        self.clear_donor()
        aligned = self.raw_index == len(self.event["raw"]) - 1
        self.current_value = {"key": key, "aligned": aligned, "entry_state": self.wrt_state(),
                              "wrt_start": self.event["end"], "raw_start": self.raw_count + self.raw_index + 1,
                              "encoded": bytearray(), "overflow": False}
        if not aligned or not fields or self.arm == "P":
            return
        first_key, first_value = fields[0]
        first_span = self.completed_spans.get(first_key)
        if first_span is None or not first_span["aligned"]:
            return
        lookup = (template, first_key, first_value, key)
        state = self.wrt_state()
        donor = self.table.get(lookup)
        if self.arm == "R":
            available = [row for ident, row in self.table.items() if ident[0] == template and ident[3] == key
                         and row["entry_state"] == state]
            donor = max(available, key=lambda row: row["serial"]) if available else None
        elif self.arm == "S":
            keys = [ident for ident, row in self.table.items() if
                    (ident[0], ident[1], ident[3]) == (template, first_key, key) and row["entry_state"] == state]
            donor = self.table[keys[(keys.index(lookup) + 1) % len(keys)]] if lookup in keys and len(keys) >= 2 else None
        if donor is not None and donor["entry_state"] != state:
            self.incompatible_lookups += 1
            donor = None
        if donor is not None:
            self.donor = donor["encoded"]
            self.activation_id += 1
            self.selected_values += 1

    def finish_field(self, key, value):
        span = self.current_value
        self.current_value = None
        if span is None:
            return
        aligned = span["aligned"] and self.raw_index == 0
        if not aligned:
            self.unaligned_values += 1
        if span["overflow"]:
            self.oversized_donors += 1
        self.completed_spans[key] = {"raw": value, "aligned": aligned,
            "encoded": None if span["overflow"] else bytes(span["encoded"]), "entry_state": span["entry_state"],
            "wrt_start": span["wrt_start"], "wrt_end": self.event["start"],
            "raw_start": span["raw_start"], "raw_end": self.raw_count + self.raw_index}

    def commit(self, template, fields):
        self.completed_invocations += 1
        if len(fields) < 2:
            return
        first_key, first_value = fields[0]
        first_span = self.completed_spans.get(first_key)
        if first_span is None or not first_span["aligned"]:
            return
        for key, value in fields[1:]:
            span = self.completed_spans.get(key)
            if span is None or not span["aligned"] or span["encoded"] is None:
                continue
            require(span["raw"] == value and span["raw_end"] - span["raw_start"] == len(value)
                    and span["wrt_end"] - span["wrt_start"] == len(span["encoded"]), "completed field span differs")
            ident = template, first_key, first_value, key
            if ident not in self.table and len(self.table) == MAX_ENTRIES:
                self.table.popitem(last=False)
                self.evictions += 1
            self.serial += 1
            self.table[ident] = {**span, "serial": self.serial}
        self.table_digest = hashlib.sha256(encoded_json(self.table_rows())).hexdigest()

    def complete_event(self, raw, kind):
        require(self.raw_count + len(raw) <= self.raw_limit, "WRT emission exceeds expected raw length")
        encoded = bytes(self.pending)
        self.event = {"start": self.event_start, "end": self.modeled_count, "raw": raw}
        previous_value = self.current_value
        if self.arm != "P":
            for self.raw_index, byte in enumerate(raw):
                self.parser.feed(byte)
            # A field beginning in this event must not include its '=' bytes.
            # A field ending in this event must not include delimiter bytes.
            if self.current_value is not None and self.current_value is previous_value:
                span = self.current_value
                if len(span["encoded"]) + len(encoded) > MAX_DONOR:
                    span["overflow"] = True
                elif not span["overflow"]:
                    span["encoded"].extend(encoded)
        self.raw_count += len(raw)
        self.raw_hash.update(raw)
        self.event_counts[kind] += 1
        self.pending.clear()
        self.event = None
        return raw

    def feed(self, modeled_byte):
        require(not self.finished and not self.failed, "adapter is closed or failed")
        try:
            require(type(modeled_byte) is int and 0 <= modeled_byte <= 255, "modeled byte must be 0..255")
            require(self.modeled_count < self.modeled_limit, "modeled work bound exceeded")
            self.modeled_count += 1
            self.modeled_hash.update(bytes([modeled_byte]))
            if not self.flag_seen:
                require(modeled_byte == wrt.TEXT_SEGMENT, "first modeled byte must be dictionary-transform flag 7")
                self.flag_seen = True
                return b""
            if not self.pending:
                self.event_start, self.event_entry = self.modeled_count - 1, self.wrt_state()
            self.pending.append(modeled_byte)
            code = bytes(wrt.wrt_byte_transform(byte) for byte in self.pending)
            first = code[0]
            if first == wrt.ESCAPE:
                return b"" if len(code) == 1 else self.complete_event(self.decoder.escaped(code[1]), "escape")
            if first in (wrt.UPPERCASE, wrt.END_UPPER, wrt.CAPITALIZED):
                self.decoder.control(first)
                return self.complete_event(b"", "control")
            if first >= 128:
                if first > 0xCF:
                    if len(code) == 1:
                        return b""
                    require(code[1] >= 0x80, "invalid WRT token continuation")
                    if code[1] > 0xCF:
                        require(first >= 0xF0 and code[1] <= 0xEF, "invalid WRT three-byte token prefix")
                        if len(code) == 2:
                            return b""
                index = wrt.token_index(code)
                require(index < len(self.words), "WRT token exceeds dictionary")
                return self.complete_event(self.decoder.word(self.words[index]), "token")
            return self.complete_event(self.decoder.literal(first), "literal")
        except Exception as error:
            self.failed, self.failure = True, type(error).__name__ + ": " + str(error)
            self.clear_donor()
            raise

    @staticmethod
    def span_view(span):
        if span is None:
            return None
        return {key: value.hex() if isinstance(value, (bytes, bytearray)) else value for key, value in span.items()}

    def table_rows(self):
        return [[*[part.hex() for part in ident], self.span_view(row)] for ident, row in self.table.items()]

    def state_digest(self):
        view = {"arm": self.arm, "raw_limit": self.raw_limit, "dictionary_digest": self.dictionary_digest,
                "raw_count": self.raw_count, "modeled_count": self.modeled_count,
                "raw_hash": self.raw_hash.hexdigest(), "modeled_hash": self.modeled_hash.hexdigest(),
                "wrt_state": self.wrt_state(), "pending": self.pending.hex(), "event_start": self.event_start,
                "event_entry": self.event_entry, "parser": self.parser.export(), "table_digest": self.table_digest,
                "serial": self.serial, "activation_id": self.activation_id, "donor": None if self.donor is None else self.donor.hex(),
                "current_value": self.span_view(self.current_value),
                "completed_spans": [[key.hex(), self.span_view(value)] for key, value in self.completed_spans.items()],
                "flag_seen": self.flag_seen, "finished": self.finished, "failed": self.failed, "failure": self.failure,
                "counts": self.stats(include_digest=False)}
        return hashlib.sha256(encoded_json(view)).hexdigest()

    def stats(self, *, include_digest=True):
        row = {"schema": "gamma.enwiki9.causal-field-WRT-adapter.v1", "arm": self.arm,
               "raw_bytes": self.raw_count, "expected_raw_bytes": self.raw_limit, "modeled_bytes": self.modeled_count,
               "modeled_limit": self.modeled_limit, "raw_sha256": self.raw_hash.hexdigest(),
               "modeled_sha256": self.modeled_hash.hexdigest(), "dictionary_sha256": self.dictionary_digest,
               "dictionary_words": len(self.words), "event_counts": dict(sorted(self.event_counts.items())),
               "associations": len(self.table), "associations_committed": self.serial, "table_digest": self.table_digest,
               "completed_invocations": self.completed_invocations, "rejected_invocations": self.rejected_invocations,
               "unaligned_values": self.unaligned_values, "oversized_donors": self.oversized_donors,
               "incompatible_lookups": self.incompatible_lookups, "selected_values": self.selected_values,
               "evictions": self.evictions, "activation_id": self.activation_id,
               "donor_bytes": None if self.donor is None else len(self.donor), "finished": self.finished,
               "failed": self.failed, "complete_package_bytes": None, "qualification_authority": False}
        if include_digest:
            row["state_digest"] = self.state_digest()
        return row

    def finish(self):
        require(not self.failed, "adapter has failed")
        require(self.flag_seen and not self.pending, "missing transform flag or incomplete WRT event")
        require(self.raw_count == self.raw_limit, "WRT raw length differs from expected length")
        self.finished = True
        return self.stats()


def source_inventory():
    return [{"path": str(path.relative_to(TOOLS.parent)), "bytes": path.stat().st_size,
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in sorted([Path(__file__), *(TOOLS / name for name in PINS)])]
