#!/usr/bin/env python3
"""Execute a fixed exact grammar while coding typed events (G/X), or raw bytes (R).

No discovery occurs here. The retained graph is an encoder input only. Definitions
precede use; content and arguments arrive when execution needs them. G and X use
the same event schedule and differ only in the kernel's interpreter-context flag.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import dualstream_grammar_v1 as old
from tools import dualstream_grammar_reserialize_v1 as rep
from tools.dualstream_event_coder_v1 import EventChannel, MODEL_SPEC

MAGIC = b"D2EVENT1"
HEADER = struct.Struct("<8sBIIQ")
FRAME = struct.Struct("<IBI32s32s")
MODES = {"R": 0, "G": 1, "X": 2}
require = old.require
sha = rep.sha
CATEGORIES = ("definitions", "program", "content", "arguments", "framing")

# Each alphabet is defined by already decoded state, never by the next value.
COUNT_PHRASES, COUNT_TEMPLATES, COUNT_RULES, COUNT_ROOTS = 1, 2, 3, 4
NODE_KIND, LITERAL_FORM, LITERAL_ID, LITERAL_LENGTH, SPELLING = 5, 6, 7, 8, 9
PHRASE_ID, ARITY, BODY_LENGTH, ARG_ID = 10, 11, 12, 13
STRUCT_KIND, CONTENT_LENGTH, TEMPLATE_ID, RULE_ID = 14, 15, 16, 17
ARG_LENGTH, ARG_BYTE, REPEATED_ARGUMENT, RAW_BYTE = 18, 19, 20, 21
SPAN_END = 22


class Interpreter:
    """One encoder/decoder transition procedure; source supplies truth only."""
    def __init__(self, channel, raw_size, source=None):
        self.ch, self.size, self.source = channel, raw_size, source
        self.pool, self.pool_ids, self.pool_bytes = [], {}, 0
        self.phrases, self.templates, self.rules = [], [], []
        self.phrase_leaves, self.phrase_sizes = [], []
        self.structure, self.content, self.arguments = [], [], []
        self.content_index, self.arg_index = 0, 0
        self.pending = []
        self.pending_consumed = 0
        self.output = bytearray()
        self.work, self.nodes, self.repeats = 0, 0, 0
        self.execution = hashlib.sha256()
        self.boundaries = hashlib.sha256()
        self.output_digest = hashlib.sha256()
        self.state_streams = {name: hashlib.sha256() for name in
            ("pool", "phrases", "templates", "rules", "structure", "content", "arguments")}

    def retain(self, name, value):
        encoded = json.dumps(rep.tagged(value), sort_keys=True, separators=(",", ":")).encode()
        self.state_streams[name].update(struct.pack("<I", len(encoded)) + encoded)

    def boundary(self, roots_completed):
        # Immutable-prefix digests bind every definition and retained binding.
        # Pending is a suffix of the latest content node's phrase expansion.
        self.boundaries.update(struct.pack("<10I", roots_completed, self.content_index,
            self.arg_index, len(self.pending), self.pending_consumed, len(self.output),
            self.work, self.nodes, self.pool_bytes, self.repeats))
        for digest in self.state_streams.values():
            self.boundaries.update(digest.digest())
        self.boundaries.update(self.output_digest.digest())
        self.boundaries.update(self.execution.digest())

    def e(self, kind, alphabet, value=None, context=(), category="program"):
        return self.ch.event(kind, alphabet, value, context=context, category=category)

    def spend(self):
        self.work += 1
        require(self.work <= 16 * old.MAX_FRAME, "execution work bound")

    def node(self):
        self.nodes += 1
        require(self.nodes <= 16 * old.MAX_FRAME, "stored instruction bound")

    def emit(self, data, context):
        require(len(self.output) + len(data) <= self.size, "output limit")
        self.output.extend(data)
        self.output_digest.update(data)
        self.ch.emit(data)
        self.execution.update(struct.pack("<4II", *context, len(data)))
        self.execution.update(data)

    def literal(self, value, context, category):
        # First-use interning serializes the existing graph's exact literal nodes.
        # It selects no new phrases or templates. Arguments are independently coded.
        exists = value in self.pool_ids if value is not None else None
        form = self.e(LITERAL_FORM, 2, int(exists) if exists is not None else None, context, category)
        if form:
            require(self.pool, "literal reference before definition")
            index = self.e(LITERAL_ID, len(self.pool), self.pool_ids[value] if value is not None else None, context, category)
            return self.pool[index]
        length = self.e(LITERAL_LENGTH, self.size + 1, len(value) if value is not None else None, context, "definitions")
        self.pool_bytes += length
        require(self.pool_bytes <= old.MAX_SECTION and len(self.pool) < 2 * old.MAX_FRAME, "literal dictionary bound")
        result = bytes(self.e(SPELLING, 256, value[i] if value is not None else None, context, "definitions") for i in range(length))
        require(result not in self.pool_ids, "duplicate literal definition")
        self.pool_ids[result] = len(self.pool)
        self.pool.append(result)
        self.retain("pool", result)
        return result

    def cp(self, value, bound, context, category="program", arity=None):
        self.node()
        kind = None if value is None else 1 if isinstance(value, old.Ref) else 2 if isinstance(value, old.Arg) else 0
        kind = self.e(NODE_KIND, 3 if arity is not None else 2, kind, context, category)
        if kind == 0:
            return self.literal(value, context, category)
        if kind == 1:
            require(bound > 0, "forward phrase reference")
            return old.Ref(self.e(PHRASE_ID, bound, value.index if value is not None else None, context, category))
        require(arity is not None and arity > 0, "invalid argument reference")
        return old.Arg(self.e(ARG_ID, arity, value.index if value is not None else None, context, category))

    def sp(self, value, bound, context):
        self.node()
        kind = None if value is None else 3 if isinstance(value, old.Ref) else {"literal": 0, "content": 1, "call": 2}[value[0]]
        kind = self.e(STRUCT_KIND, 4, kind, context)
        if kind == 0:
            return ("literal", self.literal(value[1] if value is not None else None, context, "program"))
        if kind == 1:
            return ("content", 1 + self.e(CONTENT_LENGTH, self.size, value[1] - 1 if value is not None else None, context))
        if kind == 2:
            require(self.templates, "template reference before definition")
            return ("call", self.e(TEMPLATE_ID, len(self.templates), value[1] if value is not None else None, context))
        require(bound > 0, "forward or cyclic structure reference")
        return old.Ref(self.e(RULE_ID, bound, value.index if value is not None else None, context))

    def lexical(self, value):
        return self.phrase_leaves[value.index] if isinstance(value, old.Ref) else (value,)

    def definitions(self):
        source = self.source
        count = self.e(COUNT_PHRASES, 65, len(source.phrases) if source is not None else None)
        for i in range(count):
            pair = tuple(self.cp(source.phrases[i][j] if source is not None else None, i, (1, 0, j, 0)) for j in range(2))
            leaves = tuple(leaf for value in pair for leaf in self.lexical(value))
            length = sum(map(len, leaves))
            require(length <= self.size and len(leaves) <= 2 * old.MAX_FRAME, "phrase expansion bound")
            self.phrases.append(pair)
            self.retain("phrases", pair)
            self.phrase_leaves.append(leaves)
            self.phrase_sizes.append(length)
        count = self.e(COUNT_TEMPLATES, 65 - len(self.phrases), len(source.templates) if source is not None else None)
        for i in range(count):
            context = (2, i + 1, 0, 0)
            arity = self.e(ARITY, 33, source.templates[i][0] if source is not None else None, context)
            length = self.e(BODY_LENGTH, 2 * self.size + 1, len(source.templates[i][1]) if source is not None else None, context)
            body = tuple(self.cp(source.templates[i][1][j] if source is not None else None, len(self.phrases), (2, i + 1, j, 0), arity=arity) for j in range(length))
            require({x.index for x in body if isinstance(x, old.Arg)} == set(range(arity)), "unused template argument")
            self.templates.append((arity, body))
            self.retain("templates", (arity, body))
        count = self.e(COUNT_RULES, 65 - len(self.phrases) - len(self.templates), len(source.structure_rules) if source is not None else None)
        for i in range(count):
            pair = tuple(self.sp(source.structure_rules[i][j] if source is not None else None, i, (3, 0, j, 0)) for j in range(2))
            self.rules.append(pair)
            self.retain("rules", pair)

    def argument(self, supplied, context):
        size = self.e(ARG_LENGTH, self.size + 1, len(supplied) if supplied is not None else None, context, "arguments")
        result = bytearray()
        for i in range(size):
            value = self.e(ARG_BYTE, 256, supplied[i] if supplied is not None else None, context, "arguments")
            data = bytes((value,))
            self.emit(data, context)
            result.extend(data)
        return bytes(result)

    def execute(self, root):
        stack = [root]
        while stack:
            self.spend()
            value = stack.pop()
            if isinstance(value, old.Ref):
                stack.extend(reversed(self.rules[value.index]))
                continue
            kind, index = value
            if kind == "literal":
                self.emit(index, (4, 0, 0, 0))
            elif kind == "content":
                context = (5, 0, 0, 0)
                for _ in range(index):
                    if not self.pending:
                        if self.source is not None:
                            require(self.content_index < len(self.source.content), "content exhausted")
                        item = self.cp(self.source.content[self.content_index] if self.source is not None else None, len(self.phrases), context, "content")
                        self.content_index += 1
                        self.content.append(item)
                        self.retain("content", item)
                        self.pending.extend(reversed(self.lexical(item)))
                        self.pending_consumed = 0
                    self.spend()
                    self.emit(self.pending.pop(), context)
                    self.pending_consumed += 1
                self.e(SPAN_END, 1, 0 if self.source is not None else None, context, "content")
            else:
                arity, body = self.templates[index]
                if self.source is not None:
                    require(self.arg_index + arity <= len(self.source.arguments), "arguments exhausted")
                supplied = [None] * arity
                for position, item in enumerate(body):
                    self.spend()
                    if isinstance(item, old.Arg):
                        context = (6, index + 1, position, item.index + 1)
                        if supplied[item.index] is None:
                            truth = self.source.arguments[self.arg_index + item.index] if self.source is not None else None
                            supplied[item.index] = self.argument(truth, context)
                        else:
                            self.e(REPEATED_ARGUMENT, 1, 0 if self.source is not None else None, context, "arguments")
                            self.emit(supplied[item.index], context)
                            self.repeats += 1
                    else:
                        for literal in self.lexical(item):
                            self.spend()
                            self.emit(literal, (6, index + 1, position, 0))
                require(all(x is not None for x in supplied), "unused invocation argument")
                self.arguments.extend(supplied)
                for argument in supplied:
                    self.retain("arguments", argument)
                self.arg_index += arity

    def run(self):
        self.definitions()
        self.boundary(0)
        source = self.source
        roots = self.e(COUNT_ROOTS, 2 * self.size + 1, len(source.structure) if source is not None else None)
        for i in range(roots):
            root = self.sp(source.structure[i] if source is not None else None, len(self.rules), (4, 0, 0, 0))
            self.structure.append(root)
            self.retain("structure", root)
            self.execute(root)
            self.boundary(i + 1)
        require(not self.pending and len(self.output) == self.size, "unconsumed content or incomplete frame")
        model = old.Model(tuple(self.structure), tuple(self.content), tuple(self.arguments), tuple(self.phrases), tuple(self.templates), tuple(self.rules))
        if source is not None:
            require(rep.graph(model) == rep.graph(source), "selected graph changed")
        return bytes(self.output), model, dict(interpreter_sha256=self.execution.hexdigest(), execution_steps=self.work,
                                              repeated_argument_references=self.repeats, stored_nodes=self.nodes,
                                              boundary_sha256=self.boundaries.hexdigest(), boundary_count=roots + 1)


def raw_frame(channel, size, raw=None):
    output = bytearray()
    for i in range(size):
        value = channel.event(RAW_BYTE, 256, raw[i] if raw is not None else None, context=(), category="content")
        data = bytes((value,))
        output.extend(data)
        channel.emit(data)
    return bytes(output), old.Model(), dict(interpreter_sha256=sha(bytes(output)), execution_steps=size,
                                           repeated_argument_references=0, stored_nodes=0,
                                           boundary_sha256=sha(bytes(output)), boundary_count=size)


def selected_frames(data):
    require(data[:8] == old.MAGIC, "fixed grammar input must be D2GRAM01")
    raw = old.decode(data)
    reader = old.Reader(data)
    _, frame_size, count, total = old.HEADER.unpack(reader.take(old.HEADER.size))
    frames, offset = [], 0
    for _ in range(count):
        values = old.FRAME.unpack(reader.take(old.FRAME.size))
        size, kind = values[:2]
        sections = tuple(reader.take(n) for n in values[2:7])
        model = None if kind == 0 else rep.unpack_model(sections, size, "old")
        frames.append((raw[offset:offset + size], kind, model))
        offset += size
    reader.end()
    require(offset == total, "selected frame size differs")
    return frame_size, frames


def costs_from(report):
    # The kernel assigns actual emitted arithmetic bytes to event categories.
    costs = {key: report["actual_bytes_by_category"].get(key, 0) for key in CATEGORIES}
    require(sum(costs.values()) == report["payload_bytes"], "kernel accounting differs")
    return costs


def process_frame(mode, size, kind, model=None, raw=None, payload=None):
    channel = EventChannel(mode, payload=payload)
    if kind == 0:
        restored, recovered, execution = raw_frame(channel, size, raw)
    else:
        restored, recovered, execution = Interpreter(channel, size, model).run()
    coded, synchronization = channel.finish()
    costs = costs_from(synchronization)
    costs["framing"] += FRAME.size
    result = dict(raw_bytes=size, raw_sha256=sha(restored), model_sha256=rep.fingerprint(recovered),
                  mode=kind, costs=costs, synchronization=synchronization, **execution)
    return restored, coded, result


def encode(data, mode, frame_size=old.MAX_FRAME):
    require(mode in MODES and 1 <= frame_size <= old.MAX_FRAME, "mode/frame bound")
    if mode == "R":
        require(len(data) <= old.MAX_RAW, "raw input bound")
        frames = [(data[i:i + frame_size], 0, None) for i in range(0, len(data), frame_size)]
    else:
        require(len(data) <= old.MAX_ARCHIVE, "selected archive bound")
        frame_size, frames = selected_frames(data)
    total = sum(len(raw) for raw, _, _ in frames)
    output = bytearray(HEADER.pack(MAGIC, MODES[mode], frame_size, len(frames), total))
    reports, restored = [], bytearray()
    for raw, kind, model in frames:
        inverse, payload, report = process_frame(mode, len(raw), kind, model, raw)
        require(inverse == raw, "encoder reconstruction differs")
        output.extend(FRAME.pack(len(raw), kind, len(payload), bytes.fromhex(report["raw_sha256"]), bytes.fromhex(report["model_sha256"])))
        output.extend(payload)
        require(len(output) <= old.MAX_ARCHIVE, "archive output bound")
        reports.append(report)
        restored.extend(raw)
    return bytes(output), summarize(mode, frame_size, bytes(restored), reports, len(output))


def summarize(mode, frame_size, raw, frames, size):
    costs = {key: sum(frame["costs"][key] for frame in frames) for key in CATEGORIES}
    costs["framing"] += HEADER.size
    require(sum(costs.values()) == size, "complete archive accounting differs")
    return dict(mode=mode, context_enabled=mode == "X", frame_size=frame_size, frames=frames, costs=costs, raw_bytes=len(raw), raw_sha256=sha(raw),
                complete_archive_bytes=size, model_spec=MODEL_SPEC, complete_package_bytes=None,
                cost_meanings={"definitions": "literal spelling bytes and lengths, including first-use dictionary entries",
                               "program": "grammar definitions, root instructions, calls, node tags and references",
                               "content": "executed content references and raw-baseline byte events",
                               "arguments": "first-use argument lengths and bytes, deterministic repeat events",
                               "framing": "archive/frame headers and deferred arithmetic termination/checksum bytes"},
                full_corpus_score_bytes=None, raw_encoder_repeat_proved=mode == "R",
                repeat_scope="raw-context-encoding" if mode == "R" else "fixed-graph-event-encoding")


def decode(data):
    require(len(data) <= old.MAX_ARCHIVE, "archive input bound")
    reader = old.Reader(data)
    magic, mode_id, frame_size, count, total = HEADER.unpack(reader.take(HEADER.size))
    require(magic == MAGIC and mode_id in MODES.values(), "invalid event header")
    mode = next(key for key, value in MODES.items() if value == mode_id)
    require(0 <= total <= old.MAX_RAW and 1 <= frame_size <= old.MAX_FRAME and count == (total + frame_size - 1) // frame_size, "frame count/output bound")
    output, reports = bytearray(), []
    for i in range(count):
        size, kind, length, raw_hash, graph_hash = FRAME.unpack(reader.take(FRAME.size))
        require(size == min(frame_size, total - i * frame_size) and kind in old.MODES.values() and (mode != "R" or kind == 0), "frame partition or kind differs")
        payload = reader.take(length)
        restored, _, report = process_frame(mode, size, kind, payload=payload)
        require(bytes.fromhex(report["raw_sha256"]) == raw_hash and bytes.fromhex(report["model_sha256"]) == graph_hash, "raw/graph checksum differs")
        output.extend(restored)
        reports.append(report)
    reader.end()
    return bytes(output), summarize(mode, frame_size, bytes(output), reports, len(data))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("encode", "decode"))
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mode", choices=tuple(MODES))
    args = parser.parse_args()
    start, cpu = time.monotonic(), time.process_time()
    with args.input.open("rb") as source:
        data = source.read(old.MAX_ARCHIVE + 1)
    if args.operation == "encode":
        require(args.mode is not None, "encoder mode required")
        result, report = encode(data, args.mode)
    else:
        require(args.mode is None, "decoder reads its mode from the archive")
        result, report = decode(data)
    old.new_file(args.output, lambda target: target.write(result))
    print(json.dumps(dict(result=report, cpu_seconds=time.process_time() - cpu,
                         elapsed_seconds=time.monotonic() - start,
                         peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                         complete_package_bytes=None, full_corpus_score_bytes=None), sort_keys=True))


if __name__ == "__main__":
    main()
