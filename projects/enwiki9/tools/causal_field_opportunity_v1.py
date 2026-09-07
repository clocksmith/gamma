"""Observe prefix-known opportunities in the frozen field WRT adapter.

API only: callers supply modeled bytes and a dictionary. This module neither
opens data nor runs a predictor. Diagnostics are separate from inherited codec
state and describe retained-table matches, not global selector uniqueness or
precise causes of grammar rejection. P deliberately performs no parser work.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType

BASE_ADAPTER_SHA256 = "649acd80af3ac10e8c2273bde3c2007e07d677bd2941c939494bd0ab76f7c89a"
MAX_FIRST_EVENTS = 128


def _load_adapter():
    path = Path(__file__).resolve().with_name("causal_field_wrt_adapter_v1.py")
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != BASE_ADAPTER_SHA256:
        raise ValueError("frozen WRT adapter source changed")
    module = ModuleType(__name__ + ".frozen_adapter")
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    # Execute the exact bytes authenticated above, rather than a cached module.
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


base = _load_adapter()
ELIGIBILITY = ("unaligned_entry", "no_earlier_field", "missing_first_span",
               "unaligned_first_span", "eligible")
CONDITIONAL = ("no_matching_template", "no_template_later_key",
               "no_template_first_key_later_key", "no_exact_first_value",
               "incompatible_wrt_entry_state", "exact_compatible_hit")
RECENCY = ("no_template_later_key", "no_compatible_wrt_entry_state", "compatible_route_hit")
ROTATED = ("no_exact_tuple", "incompatible_exact_entry_state",
           "missing_rotated_alternatives", "compatible_rotated_hit")


class _ObservedParser(base.FieldParser):
    def invalidate(self):
        # Repeated quarantine calls are not new invalidation transitions.
        context = self.owner._context() if self.mode != "invalid" else None
        super().invalidate()
        if context is not None:
            self.owner._invalidations += 1
            self.owner._record({"kind": "parser_invalidation", "context": context})


class Adapter(base.Adapter):
    """Frozen Adapter with bounded, observation-only diagnostic counters.

Eligibility partitions follow the original short-circuit order: current event
alignment, existence of an earlier field, then its completed aligned span.
Conditional, recency and rotated counts each partition eligible starts. They
describe matches in the current FIFO table under the current WRT entry state;
only the inherited start_value method chooses a donor.
"""

    def __init__(self, words, arm="T", raw_limit=base.MAX_RAW, *, first_event_limit=32):
        base.require(type(first_event_limit) is int and 0 <= first_event_limit <= MAX_FIRST_EVENTS,
                     "first-event diagnostic bound exceeded")
        self._first_event_limit = first_event_limit
        self._first_events = []
        self._omitted_events = 0
        self._starts = 0
        self._invalidations = 0
        self._eligibility = dict.fromkeys(ELIGIBILITY, 0)
        self._conditional = dict.fromkeys(CONDITIONAL, 0)
        self._recency = dict.fromkeys(RECENCY, 0)
        self._rotated = dict.fromkeys(ROTATED, 0)
        self._selected_starts = 0
        super().__init__(words, arm, raw_limit)
        # The replacement has exactly the same initial parser fields. Its only
        # override observes invalidate() before the base method clears context.
        self.parser = _ObservedParser(self)

    def _context(self):
        parser = self.parser
        return {"modeled_bytes_consumed": self.modeled_count,
                "raw_offset": self.raw_count + (self.raw_index if self.event is not None else 0),
                "mode": parser.mode, "invocation_bytes": parser.count,
                "depth": parser.depth, "pending_brace": parser.brace,
                "name_bytes": len(parser.name), "key_bytes": len(parser.key),
                "value_bytes": len(parser.value), "completed_fields": len(parser.fields),
                "current_value_present": self.current_value is not None,
                "current_value_aligned": None if self.current_value is None else self.current_value["aligned"]}

    def _record(self, event):
        if len(self._first_events) < self._first_event_limit:
            self._first_events.append(event)
        else:
            self._omitted_events += 1

    def _opportunity(self, template, fields, key):
        event = {"kind": "value_start", "context": self._context()}
        if self.raw_index != len(self.event["raw"]) - 1:
            eligibility = "unaligned_entry"
        elif not fields:
            eligibility = "no_earlier_field"
        else:
            span = self.completed_spans.get(fields[0][0])
            eligibility = ("missing_first_span" if span is None else
                           "unaligned_first_span" if not span["aligned"] else "eligible")
        event["eligibility"] = eligibility
        if eligibility != "eligible":
            return event

        first_key, first_value = fields[0]
        lookup = template, first_key, first_value, key
        state = self.wrt_state()
        # This bounded pass reads only previously committed associations.
        templates = targets = routes = compatible_targets = compatible_routes = 0
        for ident, row in self.table.items():
            if ident[0] != template:
                continue
            templates += 1
            if ident[3] != key:
                continue
            targets += 1
            compatible_targets += row["entry_state"] == state
            if ident[1] == first_key:
                routes += 1
                compatible_routes += row["entry_state"] == state
        exact = self.table.get(lookup)
        exact_compatible = exact is not None and exact["entry_state"] == state
        conditional = ("no_matching_template" if not templates else
                       "no_template_later_key" if not targets else
                       "no_template_first_key_later_key" if not routes else
                       "no_exact_first_value" if exact is None else
                       "incompatible_wrt_entry_state" if not exact_compatible else "exact_compatible_hit")
        recency = ("no_template_later_key" if not targets else
                   "no_compatible_wrt_entry_state" if not compatible_targets else "compatible_route_hit")
        rotated = ("no_exact_tuple" if exact is None else
                   "incompatible_exact_entry_state" if not exact_compatible else
                   "missing_rotated_alternatives" if compatible_routes < 2 else "compatible_rotated_hit")
        event.update(conditional=conditional, recency=recency, rotated=rotated,
                     matching_template_rows=templates, matching_target_rows=targets,
                     matching_route_rows=routes, compatible_target_rows=compatible_targets,
                     compatible_route_rows=compatible_routes,
                     template_hex=template.hex(), first_key_hex=first_key.hex(),
                     later_key_hex=key.hex(), first_value_bytes=len(first_value),
                     first_value_sha256=hashlib.sha256(first_value).hexdigest(),
                     wrt_entry_state=list(state))
        return event

    def start_value(self, template, fields, key):
        event = self._opportunity(template, fields, key)
        before = self.selected_values
        super().start_value(template, fields, key)
        selected = self.selected_values != before
        self._starts += 1
        self._eligibility[event["eligibility"]] += 1
        if event["eligibility"] == "eligible":
            self._conditional[event["conditional"]] += 1
            self._recency[event["recency"]] += 1
            self._rotated[event["rotated"]] += 1
        self._selected_starts += selected
        event["inherited_donor_selected"] = selected
        self._record(event)

    def diagnostics(self):
        """Return detached observations; do not add them to inherited stats()."""
        parser_incomplete = self.parser.mode != "outside" or self.parser.open_pending
        row = {"schema": "gamma.enwiki9.causal-field-opportunity.v1", "arm": self.arm,
               "base_adapter_sha256": BASE_ADAPTER_SHA256,
               "parser_enabled": self.arm != "P", "start_values": self._starts,
               "eligibility": self._eligibility, "conditional": self._conditional,
               "recency": self._recency, "rotated": self._rotated,
               "inherited_selected_starts": self._selected_starts,
               "parser_invalidation_transitions": self._invalidations,
               "first_events": self._first_events, "first_event_limit": self._first_event_limit,
               "omitted_events": self._omitted_events,
               "end_state": {"finished": self.finished, "failed": self.failed,
                             "parser_prefix_incomplete": parser_incomplete,
                             "wrt_event_incomplete": bool(self.pending) or not self.flag_seen,
                             "context": self._context()},
               "interpretation": "Prefix-known retained-table opportunities only. Invalidation context is not a precise grammar-cause classification. Incomplete prefixes become EOF observations only when the caller ends input.",
               "objective_credit_bytes": 0, "complete_package_bytes": None,
               "qualification_authority": False, "corpus_execution_authorized": False}
        return json.loads(base.encoded_json(row))


def source_inventory():
    path = Path(__file__).resolve()
    rows = base.source_inventory()
    rows.append({"path": str(path.relative_to(path.parent.parent)), "bytes": path.stat().st_size,
                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return sorted(rows, key=lambda row: row["path"])
