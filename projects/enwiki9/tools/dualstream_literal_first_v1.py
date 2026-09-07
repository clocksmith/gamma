#!/usr/bin/env python3
"""Literal-first templates, admitted by complete frame Deflate cost.

Only the encoder discovers programs. Unselected spans remain length-delimited
raw bytes. One Deflate payload contains definitions, calls and arguments.
All-plain archives use exactly the unchanged D2GRAM02 plain format.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sys
import time
import zlib

_spec = importlib.util.spec_from_file_location("_literal_first_legacy", Path(__file__).with_name("dualstream_grammar_v1.py"))
legacy = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = legacy
_spec.loader.exec_module(legacy)
Arg, Reader, CodecError = legacy.Arg, legacy.Reader, legacy.CodecError
require, uint = legacy.require, legacy.uint
HEADER, FRAME = legacy.HEADER, legacy.FRAME
MAX_RAW, MAX_FRAME, MAX_ARCHIVE = legacy.MAX_RAW, legacy.MAX_FRAME, legacy.MAX_ARCHIVE
MAGIC, PLAIN_MAGIC = b"D2LIT001", b"D2GRAM02"
MAX_RULES, MAX_NODES, MAX_STEPS = 32, 2 * MAX_FRAME, 16 * MAX_FRAME
SEARCH_SPEC = dict(max_spans=1024, max_proposals=48, max_selected_rules=8,
                   min_frame_benefit=1, span_policy="complete-pages-and-LF-lines",
                   candidate_order="covered-bytes-descending-then-canonical-template",
                   selection="best-complete-frame-reencode-per-round", deflate_level=9)
REP_KEYS = ("definitions", "program_calls", "arguments", "literal_runs", "representation_framing")


def digest(data):
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Call:
    index: int
    args: tuple


@dataclass(frozen=True)
class Program:
    rules: tuple = ()
    root: tuple = ()


def coalesce(nodes):
    result = []
    for node in nodes:
        if isinstance(node, bytes) and not node:
            continue
        if isinstance(node, bytes) and result and isinstance(result[-1], bytes):
            result[-1] += node
        else:
            result.append(node)
    return tuple(result)


def pack(program):
    """Definitions precede use. Literals and actual arguments have no pool."""
    costs = dict.fromkeys(REP_KEYS, 0)
    output = bytearray()
    def put(data, category):
        output.extend(data)
        costs[category] += len(data)
    def binding(node):
        if isinstance(node, bytes):
            return b"\x00" + uint(len(node)) + node
        require(isinstance(node, Arg), "invalid argument binding")
        return b"\x01" + uint(node.index)
    def atom(node):
        if isinstance(node, bytes):
            require(bool(node), "empty literal instruction")
            return binding(node)
        if isinstance(node, Arg):
            return binding(node)
        require(isinstance(node, Call), "invalid instruction")
        return b"\x02" + uint(node.index) + uint(len(node.args)) + b"".join(binding(x) for x in node.args)
    put(uint(len(program.rules)), "representation_framing")
    for arity, body in program.rules:
        put(uint(arity) + uint(len(body)) + b"".join(atom(x) for x in body), "definitions")
    put(uint(len(program.root)), "representation_framing")
    for node in program.root:
        if isinstance(node, bytes):
            put(atom(node), "literal_runs")
        else:
            require(isinstance(node, Call), "root argument reference")
            put(b"\x02" + uint(node.index) + uint(len(node.args)), "program_calls")
            for value in node.args:
                require(isinstance(value, bytes), "root binding is not literal")
                put(binding(value), "arguments")
    require(len(output) <= legacy.MAX_SECTION, "representation size bound")
    return bytes(output), costs


def unpack(payload):
    reader = Reader(payload)
    rules, remaining = [], MAX_NODES
    def binding(arity):
        tag = reader.take(1)[0]
        if tag == 0:
            return reader.take(reader.number(MAX_FRAME))
        require(tag == 1 and arity > 0, "invalid argument tag")
        return Arg(reader.number(arity - 1))
    def atom(rule_limit, arity):
        nonlocal remaining
        remaining -= 1
        require(remaining >= 0, "stored instruction bound")
        tag = reader.take(1)[0]
        if tag == 0:
            value = reader.take(reader.number(MAX_FRAME))
            require(bool(value), "empty literal instruction")
            return value
        if tag == 1:
            require(arity > 0, "root or empty-arity reference")
            return Arg(reader.number(arity - 1))
        require(tag == 2 and rule_limit > 0, "unknown or forward rule reference")
        index = reader.number(rule_limit - 1)
        count = reader.number(32)
        require(count == rules[index][0], "call arity differs")
        remaining -= count
        require(remaining >= 0, "binding instruction bound")
        return Call(index, tuple(binding(arity) for _ in range(count)))
    for index in range(reader.number(MAX_RULES)):
        arity, count = reader.number(32), reader.number(MAX_NODES)
        require(count > 0, "empty rule")
        body = tuple(atom(index, arity) for _ in range(count))
        used = set()
        for node in body:
            values = node.args if isinstance(node, Call) else (node,)
            used.update(x.index for x in values if isinstance(x, Arg))
        require(used == set(range(arity)), "unused or missing rule arguments")
        require(coalesce(body) == body, "noncanonical adjacent literals")
        rules.append((arity, body))
    root = tuple(atom(len(rules), 0) for _ in range(reader.number(MAX_NODES)))
    require(coalesce(root) == root, "noncanonical root literals")
    reader.end()
    program = Program(tuple(rules), root)
    require(pack(program)[0] == payload, "noncanonical program encoding")
    return program


def execute(program, expected_size):
    """Backward calls terminate; explicit work/output bounds also cover empties."""
    output, used, steps, calls, repeats = bytearray(), set(), 0, 0, 0
    boundary = hashlib.sha256()
    def spend():
        nonlocal steps
        steps += 1
        require(steps <= MAX_STEPS, "expansion work bound")
    def emit(value):
        require(len(output) + len(value) <= expected_size, "expansion output bound")
        output.extend(value)
    def invoke(call, caller_args, limit):
        nonlocal calls, repeats
        spend()
        require(0 <= call.index < limit, "forward rule call")
        used.add(call.index)
        arity, body = program.rules[call.index]
        require(len(call.args) == arity, "call arity differs")
        values = tuple(caller_args[x.index] if isinstance(x, Arg) else x for x in call.args)
        require(all(isinstance(x, bytes) for x in values), "invalid resolved arguments")
        references = [0] * arity
        calls += 1
        for node in body:
            spend()
            if isinstance(node, bytes):
                emit(node)
            elif isinstance(node, Arg):
                require(0 <= node.index < arity, "argument index bound")
                references[node.index] += 1
                emit(values[node.index])
            else:
                for value in node.args:
                    if isinstance(value, Arg):
                        require(0 <= value.index < arity, "nested argument index bound")
                        references[value.index] += 1
                invoke(node, values, call.index)
        require(all(references), "unconsumed invocation argument")
        repeats += sum(n - 1 for n in references)
        boundary.update(uint(call.index) + uint(len(output)) + hashlib.sha256(output).digest())
    for node in program.root:
        spend()
        if isinstance(node, bytes):
            emit(node)
        else:
            require(isinstance(node, Call) and all(isinstance(x, bytes) for x in node.args), "invalid root")
            invoke(node, (), len(program.rules))
    require(used == set(range(len(program.rules))), "unused template definition")
    require(len(output) == expected_size, "expanded size differs")
    return bytes(output), dict(calls=calls, repeated_argument_references=repeats,
                               execution_steps=steps, boundary_sha256=boundary.hexdigest())


def frame_from_program(raw, program):
    payload, representation_costs = pack(program)
    validated = unpack(payload)
    inverse, execution = execute(validated, len(raw))
    require(inverse == raw, "candidate inverse differs")
    compressed = zlib.compress(payload, 9)
    frame = FRAME.pack(len(raw), 4, 0, 0, 0, len(compressed), 0, hashlib.sha256(raw).digest()) + compressed
    report = dict(raw_bytes=len(raw), raw_sha256=digest(raw), output_sha256=digest(inverse), mode="template",
                  complete_frame_bytes=len(frame), selected_rules=len(program.rules),
                  representation_sha256=digest(payload), program_sha256=digest(payload),
                  representation_costs=representation_costs,
                  costs=dict(deflate_payload=len(compressed), framing=FRAME.size), **execution)
    return frame, report


def plain_frame(raw):
    frame = legacy.frame_bytes(raw, "plain")[0]
    report = dict(raw_bytes=len(raw), raw_sha256=digest(raw), output_sha256=digest(raw), mode="plain",
                  complete_frame_bytes=len(frame), selected_rules=0, calls=0, repeated_argument_references=0,
                  representation_sha256=digest(raw), program_sha256=digest(b""),
                  representation_costs=dict(definitions=0, program_calls=0, arguments=0,
                                            literal_runs=len(raw), representation_framing=0),
                  costs=dict(deflate_payload=len(frame) - FRAME.size, framing=FRAME.size),
                  execution_steps=1, boundary_sha256=digest(b""))
    return frame, report


def discover(raw):
    """Bounded raw span pool; page/line overlap is resolved at admission."""
    pages = [(m.start(), m.end()) for m in legacy.PAGE.finditer(raw)]
    lines, start = [], 0
    parts = raw.split(b"\n")
    for i, part in enumerate(parts):
        part += b"\n" if i < len(parts) - 1 else b""
        if not part:
            continue
        lines.append((start, start + len(part)))
        start += len(part)
    require(start == len(raw), "span partition differs")
    all_spans = sorted(set(pages + lines))
    spans = all_spans[:SEARCH_SPEC["max_spans"]]
    chunks = [raw[a:b] for a, b in spans]
    proposals = []
    for template, uses in legacy.template_proposals(chunks):
        arity, body = template
        normalized = (arity, coalesce(body))
        proposals.append((normalized, tuple((spans[i][0], spans[i][1], args) for i, args in uses)))
    total_proposals = len(proposals)
    proposals = proposals[:SEARCH_SPEC["max_proposals"]]
    identity = hashlib.sha256()
    for rule, uses in proposals:
        identity.update(repr((rule, uses)).encode("ascii"))
    return proposals, dict(total_spans=len(all_spans), spans=len(spans),
                           spans_truncated=len(all_spans) - len(spans), total_proposals=total_proposals,
                           proposals=len(proposals), proposals_truncated=total_proposals - len(proposals),
                           proposal_sha256=identity.hexdigest())


def build_program(raw, rules, selected):
    nodes, position = [], 0
    for start, end, call in sorted(selected, key=lambda x: x[:2]):
        require(position <= start < end <= len(raw), "overlapping selected spans")
        nodes.extend((raw[position:start], call))
        position = end
    nodes.append(raw[position:])
    return Program(tuple(rules), coalesce(nodes))


def encode_frame(raw, mode):
    require(mode in ("K", "D") and 0 < len(raw) <= MAX_FRAME, "frame input or mode bound")
    current, report = plain_frame(raw)
    proposals, search = discover(raw)
    rules, selected, admitted, evaluations = [], [], set(), []
    for round_index in range(SEARCH_SPEC["max_selected_rules"]):
        options = []
        for proposal_id, (rule, uses) in enumerate(proposals):
            if proposal_id in admitted:
                continue
            available = []
            for start, end, args in sorted(uses, key=lambda x: x[:2]):
                if all(end <= a or start >= b for a, b, _ in selected + available):
                    available.append((start, end, Call(len(rules), args)))
            if len(available) < 2:
                continue
            candidate = build_program(raw, rules + [rule], selected + available)
            frame, info = frame_from_program(raw, candidate)
            row = dict(round=round_index, proposal=proposal_id, uses=len(available), before=len(current),
                       candidate=len(frame), delta=len(current) - len(frame), accepted=False,
                       candidate_sha256=digest(frame))
            evaluations.append(row)
            options.append((len(frame), proposal_id, frame, info, available, row))
        if not options:
            break
        size, proposal_id, frame, info, available, row = min(options, key=lambda x: x[:2])
        if mode == "K" or len(current) - size < SEARCH_SPEC["min_frame_benefit"]:
            break
        row["accepted"] = True
        admitted.add(proposal_id)
        rules.append(proposals[proposal_id][0])
        selected.extend(available)
        current, report = frame, info
    search.update(evaluations=evaluations, admitted=len(admitted),
                  admission_enabled=mode == "D", discovery_from_raw=True)
    report["search"] = search
    return current, report


def encode(raw, mode="D", frame_size=MAX_FRAME):
    require(isinstance(raw, bytes) and len(raw) <= MAX_RAW and 1 <= frame_size <= MAX_FRAME,
            "raw input or frame bound")
    require(mode in ("K", "D"), "unknown encoder arm")
    frames = [encode_frame(raw[i:i + frame_size], mode) for i in range(0, len(raw), frame_size)]
    magic = MAGIC if any(report["mode"] == "template" for _, report in frames) else PLAIN_MAGIC
    archive = HEADER.pack(magic, frame_size, len(frames), len(raw)) + b"".join(frame for frame, _ in frames)
    reports = [report for _, report in frames]
    report = report_for(raw, archive, frame_size, reports)
    report.update(mode=mode, search_spec=SEARCH_SPEC, repeat_scope="raw-discovery-and-encoding",
                  raw_encoder_repeat_proved=False)
    return archive, report


def report_for(raw, archive, frame_size, reports):
    return dict(raw_bytes=len(raw), raw_sha256=digest(raw), complete_archive_bytes=len(archive),
                archive_sha256=digest(archive), frame_size=frame_size, frames=reports,
                costs=dict(deflate_payload=sum(r["costs"]["deflate_payload"] for r in reports),
                           framing=HEADER.size + len(reports) * FRAME.size),
                backend="zlib9", zlib_version=zlib.ZLIB_RUNTIME_VERSION,
                complete_package_bytes=None, full_corpus_score_bytes=None,
                accounting="Joint Deflate payload and framing are additive archive bytes; representation_costs are pre-Deflate bytes, not compressed attribution.")


def decode(archive, max_output=MAX_RAW):
    require(isinstance(archive, bytes) and len(archive) <= MAX_ARCHIVE, "archive input bound")
    reader = Reader(archive)
    magic, frame_size, count, total = HEADER.unpack(reader.take(HEADER.size))
    require(magic in (MAGIC, PLAIN_MAGIC) and 1 <= frame_size <= MAX_FRAME
            and total <= min(max_output, MAX_RAW), "archive header or output bound")
    require(count == (total + frame_size - 1) // frame_size, "frame count differs")
    output, reports = bytearray(), []
    for index in range(count):
        start = reader.pos
        raw_size, mode, *fields = FRAME.unpack(reader.take(FRAME.size))
        lengths, expected_hash = fields[:5], fields[5]
        require(raw_size == min(frame_size, total - index * frame_size), "frame identity differs")
        require(mode in (0, 4) and (magic == MAGIC or mode == 0), "invalid frame mode")
        require(all(lengths[i] == 0 for i in (0, 1, 2, 4)) and lengths[3] <= 2 * legacy.MAX_SECTION,
                "invalid frame sections")
        payload = legacy.inflate(reader.take(lengths[3]))
        if mode == 0:
            raw = payload
            canonical, info = plain_frame(raw)
        else:
            program = unpack(payload)
            raw, _ = execute(program, raw_size)
            canonical, info = frame_from_program(raw, program)
        require(len(raw) == raw_size and hashlib.sha256(raw).digest() == expected_hash, "raw checksum differs")
        require(canonical == archive[start:reader.pos], "noncanonical compressed frame")
        output.extend(raw)
        reports.append(info)
    reader.end()
    require(magic == (MAGIC if any(r["mode"] == "template" for r in reports) else PLAIN_MAGIC),
            "noncanonical archive identity")
    raw = bytes(output)
    return raw, report_for(raw, archive, frame_size, reports)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("encode", "decode"))
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mode", choices=("K", "D"), default="D")
    parser.add_argument("--frame-size", type=int, default=MAX_FRAME)
    args = parser.parse_args()
    start, cpu = time.monotonic(), time.process_time()
    maximum = MAX_RAW if args.operation == "encode" else MAX_ARCHIVE
    with args.input.open("rb") as source:
        data = source.read(maximum + 1)
    require(len(data) <= maximum, "input size bound")
    output, report = (encode(data, args.mode, args.frame_size) if args.operation == "encode" else decode(data))
    legacy.new_file(args.output, lambda target: target.write(output))
    print(json.dumps(dict(result=report, cpu_seconds=time.process_time() - cpu,
                          elapsed_seconds=time.monotonic() - start,
                          peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                          complete_package_bytes=None, full_corpus_score_bytes=None), sort_keys=True))


if __name__ == "__main__":
    main()
