#!/usr/bin/env python3
"""Synthetic-only immediately preceding field selector over the frozen WRT API.

T/K/R/S share one FIFO128 table of adjacent completed fields. O retains the
original first-field table. P skips parser bookkeeping. Probability injection
belongs to the caller: K must use the unchanged parent, while T/O/R/S may use
the frozen ParentMixture. No parser, WRT event, or arithmetic semantics change.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
from types import ModuleType

TOOLS = Path(__file__).resolve().parent
BASE_SHA256 = "649acd80af3ac10e8c2273bde3c2007e07d677bd2941c939494bd0ab76f7c89a"
POLICY = "causal-field-immediately-preceding-synthetic-v1"
MAX_RAW = 8192

_path = TOOLS / "causal_field_wrt_adapter_v1.py"
_source = _path.read_bytes()
if hashlib.sha256(_source).hexdigest() != BASE_SHA256:
    raise ValueError("frozen WRT adapter source changed")
base = ModuleType(__name__ + ".frozen_adapter")
base.__file__ = str(_path)
sys.modules[base.__name__] = base
exec(compile(_source, str(_path), "exec"), base.__dict__)


class Adapter(base.Adapter):
    """Select the last completed field; commit only at valid invocation close."""
    policy_id = POLICY

    def __init__(self, words, arm="T", raw_limit=MAX_RAW):
        base.require(type(raw_limit) is int and 0 <= raw_limit <= MAX_RAW,
                     "synthetic expected raw length exceeds 8192-byte bound")
        base.require(isinstance(arm, str) and len(arm) == 1 and arm in "PKTORS", "unknown arm")
        super().__init__(words, "T" if arm == "O" else arm, raw_limit)
        self.arm = arm

    def start_value(self, template, fields, key):
        # The existing lookup retains alignment, entry-state and R/S behavior.
        super().start_value(template, fields if self.arm == "O" else fields[-1:], key)

    def commit(self, template, fields):
        if self.arm == "O":
            return super().commit(template, fields)
        self.completed_invocations += 1
        if len(fields) < 2:
            return
        for (previous_key, previous_value), (key, value) in zip(fields, fields[1:]):
            previous = self.completed_spans.get(previous_key)
            span = self.completed_spans.get(key)
            if previous is None or not previous["aligned"]:
                continue
            if span is None or not span["aligned"] or span["encoded"] is None:
                continue
            base.require(span["raw"] == value and span["raw_end"] - span["raw_start"] == len(value)
                         and span["wrt_end"] - span["wrt_start"] == len(span["encoded"]),
                         "completed field span differs")
            ident = template, previous_key, previous_value, key
            if ident not in self.table and len(self.table) == base.MAX_ENTRIES:
                self.table.popitem(last=False)
                self.evictions += 1
            self.serial += 1
            self.table[ident] = {**span, "serial": self.serial}
        self.table_digest = hashlib.sha256(base.encoded_json(self.table_rows())).hexdigest()

    def state_digest(self):
        return hashlib.sha256((self.policy_id + "\0" + super().state_digest()).encode()).hexdigest()


def source_inventory():
    paths = [Path(__file__), *(TOOLS.parent / row["path"] for row in base.source_inventory())]
    return [{"path": str(path.relative_to(TOOLS.parent)), "bytes": path.stat().st_size,
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in sorted(paths)]
