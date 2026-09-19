#!/usr/bin/env python3
"""Standalone exact two-stream grammar; frame lookahead, no learned decoder.

The structure stream contains a shared literal pool, backward phrase programs,
parameter templates and root instructions. The content stream contains lexical
references and invocation arguments. Five separately Deflated sections make
every byte category additive, including backend tables. There is no model or
external codec dependency beyond Python's standard-library zlib.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import struct
import tempfile
import time
import zlib

MAGIC = b"D2GRAM01"
HEADER = struct.Struct("<8sIIQ")
FRAME = struct.Struct("<IB5I32s")
MAX_RAW = 1_000_000
MAX_FRAME = 65_536
MAX_SECTION = 16 * MAX_FRAME
MAX_ARCHIVE = 8 * MAX_RAW
MODES = {"plain": 0, "split": 1, "grammar": 2, "parameter": 3}
TOKEN = re.compile(rb"<[A-Za-z_/!?][^<>]{0,2048}>|[A-Za-z]+|[0-9]+|[ \t\r\n\v\f]+|[\s\S]")
MARKUP = re.compile(rb"<[A-Za-z_/!?][^<>]{0,2048}>")
PAGE = re.compile(rb"<page>.*?</page>(?:\r?\n)?", re.S)


class CodecError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise CodecError(message)


def uint(value):
    require(type(value) is int and 0 <= value < 2**63, "integer out of range")
    result = bytearray()
    while value >= 128:
        result.append((value & 127) | 128)
        value >>= 7
    result.append(value)
    return bytes(result)


class Reader:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def take(self, size):
        require(0 <= size <= len(self.data) - self.pos, "truncated section")
        data = self.data[self.pos:self.pos + size]
        self.pos += size
        return data

    def number(self, maximum=MAX_SECTION):
        value = 0
        for shift in range(0, 63, 7):
            byte = self.take(1)[0]
            value |= (byte & 127) << shift
            if byte < 128:
                require(value <= maximum and (shift == 0 or byte != 0), "invalid integer")
                return value
        raise CodecError("oversized integer")

    def end(self):
        require(self.pos == len(self.data), "trailing section bytes")


@dataclass(frozen=True)
class Ref:
    index: int


@dataclass(frozen=True)
class Arg:
    index: int


@dataclass(frozen=True)
class Config:
    max_rule_length: int = 8
    grammar_budget: int = 16
    min_benefit: int = 1
    shortlist: int = 4

    def validate(self):
        require(2 <= self.max_rule_length <= 32, "rule length bound")
        require(0 <= self.grammar_budget <= 64, "grammar budget bound")
        require(1 <= self.min_benefit <= 1024, "minimum benefit bound")
        require(1 <= self.shortlist <= 8, "shortlist bound")


@dataclass(frozen=True)
class Model:
    structure: tuple = ()
    content: tuple = ()
    arguments: tuple = ()
    phrases: tuple = ()
    templates: tuple = ()  # (arity, body of bytes / earlier phrase Ref / Arg)
    structure_rules: tuple = ()


def tokenize(data):
    return TOKEN.findall(data)


def records(raw):
    """Complete bounded page fragments, with exact LF records for their gaps."""
    result, start = [], 0
    def lines(data):
        parts = data.split(b"\n")
        result.extend(p + b"\n" for p in parts[:-1])
        if parts[-1]:
            result.append(parts[-1])
    for match in PAGE.finditer(raw):
        lines(raw[start:match.start()])
        result.append(match.group())
        start = match.end()
    lines(raw[start:])
    require(b"".join(result) == raw, "record partition changed bytes")
    return result


def model_for(chunks, selected=(), templates=()):
    selected = dict(selected)
    structure, content, arguments = [], [], []
    for index, data in enumerate(chunks):
        if index in selected:
            template, args = selected[index]
            structure.append(("call", template))
            arguments.extend(args)
            continue
        for token in tokenize(data):
            if MARKUP.fullmatch(token):
                structure.append(("literal", token))
            else:
                content.append(token)
                if structure and structure[-1][0] == "content":
                    structure[-1] = ("content", structure[-1][1] + 1)
                else:
                    structure.append(("content", 1))
    return Model(tuple(structure), tuple(content), tuple(arguments), templates=tuple(templates))


def packed_sections(model):
    """Pool only reachable literal spellings; program references precede use."""
    pool, ids = [], {}
    def literal(value):
        if value not in ids:
            ids[value] = len(pool)
            pool.append(value)
        return ids[value]
    def cp(value):
        return uint(2 * value.index + 1) if isinstance(value, Ref) else uint(2 * literal(value))
    def sp(value):
        if isinstance(value, Ref):
            return uint(4 * value.index + 3)
        kind, data = value
        if kind == "literal":
            return uint(4 * literal(data))
        if kind == "content":
            return uint(4 * (data - 1) + 1)
        require(kind == "call", "unknown structure instruction")
        return uint(4 * data + 2)
    programs = bytearray(uint(len(model.phrases)))
    for pair in model.phrases:
        programs.extend(b"".join(cp(x) for x in pair))
    programs.extend(uint(len(model.templates)))
    for arity, body in model.templates:
        programs.extend(uint(arity) + uint(len(body)))
        for value in body:
            if isinstance(value, Arg):
                programs.extend(uint(2 * value.index + 1))
            else:
                encoded = Reader(cp(value)).number()
                programs.extend(uint(2 * encoded))
    programs.extend(uint(len(model.structure_rules)))
    for pair in model.structure_rules:
        programs.extend(b"".join(sp(x) for x in pair))
    structure = uint(len(model.structure)) + b"".join(sp(x) for x in model.structure)
    content = uint(len(model.content)) + b"".join(cp(x) for x in model.content)
    arguments = uint(len(model.arguments)) + b"".join(uint(literal(x)) for x in model.arguments)
    definitions = uint(len(pool)) + b"".join(uint(len(x)) + x for x in pool)
    sections = (definitions, bytes(programs), structure, content, arguments)
    require(all(len(x) <= MAX_SECTION for x in sections), "section size bound")
    return tuple(zlib.compress(x, 9) if x else b"" for x in sections)


def frame_bytes(raw, mode, model=None):
    sections = (b"", b"", b"", zlib.compress(raw, 9), b"") if mode == "plain" else packed_sections(model)
    header = FRAME.pack(len(raw), MODES[mode], *(len(x) for x in sections), hashlib.sha256(raw).digest())
    sizes = dict(literal_definition_bytes=len(sections[0]), structure_bytes=len(sections[1]) + len(sections[2]),
                 content_bytes=len(sections[3]), argument_reference_bytes=len(sections[4]), exception_bytes=0,
                 framing_bytes=len(header), complete_archive_bytes=len(header) + sum(map(len, sections)))
    return header + b"".join(sections), sizes


def replace_pair(sequence, pair, symbol):
    output, index = [], 0
    while index < len(sequence):
        if tuple(sequence[index:index + 2]) == pair:
            output.append(symbol)
            index += 2
        else:
            output.append(sequence[index])
            index += 1
    return tuple(output)


def factor(raw, start, config, decisions):
    """Occurrence counts shortlist proposals; only complete frame bytes select."""
    model = start
    current = len(frame_bytes(raw, "grammar", model)[0])
    while len(model.phrases) + len(model.structure_rules) + len(model.templates) < config.grammar_budget:
        proposals = []
        for stream in ("content", "structure"):
            seq = getattr(model, stream)
            counts = Counter(zip(seq, seq[1:]))
            if stream == "content":
                for _, body in model.templates:
                    counts.update((a, b) for a, b in zip(body, body[1:]) if not isinstance(a, Arg) and not isinstance(b, Arg))
            rules = model.phrases if stream == "content" else model.structure_rules
            lengths = []
            for pair in rules:
                lengths.append(sum(lengths[x.index] if isinstance(x, Ref) else 1 for x in pair))
            top = sorted(counts, key=lambda p: (-counts[p], repr(p)))[:config.shortlist]
            for pair in top:
                if counts[pair] < 2 or sum(lengths[x.index] if isinstance(x, Ref) else 1 for x in pair) > config.max_rule_length:
                    continue
                symbol = Ref(len(rules))
                if stream == "content":
                    templates = tuple((n, replace_pair(body, pair, symbol)) for n, body in model.templates)
                    candidate = replace(model, phrases=rules + (pair,), content=replace_pair(seq, pair, symbol), templates=templates)
                else:
                    candidate = replace(model, structure_rules=rules + (pair,), structure=replace_pair(seq, pair, symbol))
                size = len(frame_bytes(raw, "grammar", candidate)[0])
                proposals.append((size, stream, repr(pair), candidate))
        if not proposals:
            break
        size, stream, description, best = min(proposals, key=lambda x: x[:3])
        decisions.append(dict(kind="phrase", stream=stream, proposed=len(proposals), before=current, best=size, accepted=current - size >= config.min_benefit))
        if current - size < config.min_benefit:
            break
        model, current = best, size
    return model


def split_schema(data):
    matches = list(MARKUP.finditer(data))
    if matches and len(matches) <= 128:
        chunks, start = [], 0
        for match in matches:
            chunks.append(data[start:match.start()])
            start = match.end()
        chunks.append(data[start:])
        return ("xml", tuple(m.group() for m in matches)), tuple(chunks)
    tokens = tokenize(data)
    if not 2 <= len(tokens) <= 128:
        return None
    key, chunks = [], []
    for token in tokens:
        if re.fullmatch(rb"[A-Za-z]+|[0-9]+", token):
            key.append(None)
            chunks.append(token)
        else:
            key.append(token)
    return ("text", tuple(key)), tuple(chunks)


def common_ends(values):
    first, last = min(values), max(values)
    prefix = 0
    while prefix < min(len(first), len(last)) and first[prefix] == last[prefix]:
        prefix += 1
    suffix = 0
    limit = min(map(len, values)) - prefix
    while suffix < limit and len({v[len(v) - 1 - suffix] for v in values}) == 1:
        suffix += 1
    return first[:prefix], first[len(first) - suffix:] if suffix else b""


def template_proposals(chunks):
    groups = defaultdict(list)
    for index, data in enumerate(chunks):
        parsed = split_schema(data)
        if parsed is not None and parsed[1]:
            groups[parsed[0]].append((index, parsed[1]))
    proposals = []
    for key, members in groups.items():
        if len(members) < 2:
            continue
        columns = list(zip(*(values for _, values in members), strict=True))
        ends = [common_ends(values) for values in columns]
        varying = [len(set(values)) > 1 for values in columns]
        if not any(varying):
            continue
        partitions = defaultdict(list)
        for index, values in members:
            supplied, pattern = [], []
            for value, (prefix, suffix), variable in zip(values, ends, varying):
                if variable:
                    middle = value[len(prefix):len(value) - len(suffix) if suffix else len(value)]
                    if middle not in supplied:
                        supplied.append(middle)
                    pattern.append(supplied.index(middle))
            if len(supplied) <= 32:
                partitions[tuple(pattern)].append((index, tuple(supplied)))
        for pattern, uses in partitions.items():
            if len(uses) < 2:
                continue
            body, variable_index = [], 0
            def column(i):
                nonlocal variable_index
                if varying[i]:
                    body.extend(tokenize(ends[i][0]))
                    body.append(Arg(pattern[variable_index]))
                    variable_index += 1
                    body.extend(tokenize(ends[i][1]))
                else:
                    body.extend(tokenize(columns[i][0]))
            if key[0] == "xml":
                for i, markup in enumerate(key[1]):
                    column(i)
                    body.append(markup)
                column(len(key[1]))
            else:
                i = 0
                for item in key[1]:
                    if item is None:
                        column(i)
                        i += 1
                    else:
                        body.append(item)
            arity = max(pattern) + 1
            template = (arity, tuple(body))
            for index, values in uses:
                expanded = b"".join(values[x.index] if isinstance(x, Arg) else x for x in body)
                require(expanded == chunks[index], "template discovery changed bytes")
            proposals.append((template, tuple(uses)))
    return sorted(proposals, key=lambda p: (-sum(len(chunks[i]) for i, _ in p[1]), repr(p[0])))


def parameterize(raw, chunks, config, decisions):
    selected, templates = {}, []
    model = model_for(chunks)
    current = len(frame_bytes(raw, "parameter", model)[0])
    for template, uses in template_proposals(chunks)[:32]:
        if len(templates) >= config.grammar_budget:
            break
        available = [(i, a) for i, a in uses if i not in selected]
        if len(available) < 2:
            continue
        mapping = dict(selected)
        mapping.update((i, (len(templates), args)) for i, args in available)
        candidate = model_for(chunks, mapping.items(), templates + [template])
        size = len(frame_bytes(raw, "parameter", candidate)[0])
        gain = current - size
        decisions.append(dict(kind="template", occurrences=len(available), arity=template[0],
                              argument_uses=sum(isinstance(x, Arg) for x in template[1]), before=current,
                              best=size, accepted=gain >= config.min_benefit))
        if gain >= config.min_benefit:
            selected, templates, model, current = mapping, templates + [template], candidate, size
    return factor(raw, model, config, decisions)


def encode_frame(raw, mode, config):
    require(0 < len(raw) <= MAX_FRAME, "frame input bound")
    require(mode in (*MODES, "auto"), "unknown mode")
    decisions = []
    plain = frame_bytes(raw, "plain")
    if mode == "plain":
        return plain[0], dict(plain[1], mode="plain", raw_bytes=len(raw), decisions=[], templates=0, supplied_arguments=0, repeated_argument_references=0)
    chunks = records(raw)
    split = model_for(chunks)
    chosen_model = split
    if mode == "split":
        encoded, sizes = frame_bytes(raw, "split", split)
    else:
        grammar = factor(raw, split, config, decisions)
        chosen_model = grammar
        encoded, sizes = frame_bytes(raw, "grammar", grammar)
        chosen = "grammar"
        if mode in ("parameter", "auto"):
            parameter = parameterize(raw, chunks, config, decisions)
            candidate, costs = frame_bytes(raw, "parameter", parameter)
            if len(candidate) < len(encoded):
                encoded, sizes, chosen = candidate, costs, "parameter"
                chosen_model = parameter
        if mode == "auto":
            alternatives = [(len(encoded), 1, encoded, sizes, chosen), (len(plain[0]), 0, *plain, "plain")]
            _, _, encoded, sizes, chosen = min(alternatives, key=lambda x: x[:2])
            if chosen == "plain":
                chosen_model = Model()
        mode = chosen
    calls = Counter()
    stack = list(chosen_model.structure)
    while stack:
        item = stack.pop()
        if isinstance(item, Ref):
            stack.extend(chosen_model.structure_rules[item.index])
        elif item[0] == "call":
            calls[item[1]] += 1
    reused = sum(calls[i] * (sum(isinstance(v, Arg) for v in body) - arity)
                 for i, (arity, body) in enumerate(chosen_model.templates))
    return encoded, dict(sizes, mode=mode, raw_bytes=len(raw), decisions=decisions,
                         templates=len(chosen_model.templates), supplied_arguments=len(chosen_model.arguments),
                         repeated_argument_references=reused)


def inflate(data):
    if not data:
        return b""
    decoder = zlib.decompressobj()
    try:
        result = decoder.decompress(data, MAX_SECTION + 1)
    except zlib.error as error:
        raise CodecError("invalid Deflate section") from error
    require(len(result) <= MAX_SECTION and decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail,
            "oversized, truncated or trailing Deflate section")
    return result


def interpret(sections, raw_size):
    pool_reader, programs, structure, content, arguments = [Reader(inflate(x)) for x in sections]
    pool = [pool_reader.take(pool_reader.number(MAX_SECTION)) for _ in range(pool_reader.number(2 * MAX_FRAME))]
    pool_reader.end()
    phrases, templates, structure_rules = [], [], []
    phrase_lengths = []
    def cp(code, bound):
        index, kind = code >> 1, code & 1
        require(index < (bound if kind else len(pool)), "forward or invalid phrase reference")
        return Ref(index) if kind else pool[index]
    def cp_length(value):
        return phrase_lengths[value.index] if isinstance(value, Ref) else len(value)
    for i in range(programs.number(64)):
        pair = tuple(cp(programs.number(), i) for _ in range(2))
        length = sum(cp_length(x) for x in pair)
        require(length <= raw_size, "phrase expansion limit")
        phrases.append(pair)
        phrase_lengths.append(length)
    for _ in range(programs.number(64)):
        arity, count = programs.number(32), programs.number(2 * MAX_FRAME)
        body = []
        for _ in range(count):
            code = programs.number()
            if code & 1:
                require(code >> 1 < arity, "argument reference out of range")
                body.append(Arg(code >> 1))
            else:
                body.append(cp(code >> 1, len(phrases)))
        require({v.index for v in body if isinstance(v, Arg)} == set(range(arity)), "unused template argument")
        templates.append((arity, tuple(body)))
    def sp(code, bound):
        index, kind = code >> 2, code & 3
        if kind == 0:
            require(index < len(pool), "invalid structure literal")
            return ("literal", pool[index])
        if kind == 1:
            require(index < raw_size, "content run limit")
            return ("content", index + 1)
        if kind == 2:
            require(index < len(templates), "forward or invalid template reference")
            return ("call", index)
        require(index < bound, "forward or cyclic structure rule")
        return Ref(index)
    for i in range(programs.number(64)):
        structure_rules.append(tuple(sp(programs.number(), i) for _ in range(2)))
    programs.end()
    require(len(phrases) + len(templates) + len(structure_rules) <= 64, "total grammar budget")
    content_refs = [cp(content.number(), len(phrases)) for _ in range(content.number(2 * MAX_FRAME))]
    content.end()
    arg_values = []
    for _ in range(arguments.number(2 * MAX_FRAME)):
        index = arguments.number()
        require(index < len(pool), "invalid supplied argument")
        arg_values.append(pool[index])
    arguments.end()
    roots = [sp(structure.number(), len(structure_rules)) for _ in range(structure.number(2 * MAX_FRAME))]
    structure.end()
    work_left = 16 * MAX_FRAME
    def spend():
        nonlocal work_left
        work_left -= 1
        require(work_left >= 0, "program expansion work limit")
    def expand(values, rules):
        stack = list(reversed(values))
        while stack:
            value = stack.pop()
            spend()
            if isinstance(value, Ref):
                stack.extend(reversed(rules[value.index]))
            else:
                yield value
    lexical = iter(expand(content_refs, phrases))
    output, consumed = bytearray(), 0
    def emit(data):
        require(len(output) + len(data) <= raw_size, "decoded output limit")
        output.extend(data)
    for kind, value in expand(roots, structure_rules):
        if kind == "literal":
            emit(value)
        elif kind == "content":
            for _ in range(value):
                literal = next(lexical, None)
                require(literal is not None, "content stream exhausted")
                emit(literal)
        else:
            arity, body = templates[value]
            require(consumed + arity <= len(arg_values), "argument stream exhausted")
            supplied = arg_values[consumed:consumed + arity]
            consumed += arity
            for item in body:
                spend()
                if isinstance(item, Arg):
                    emit(supplied[item.index])
                else:
                    for literal in expand((item,), phrases):
                        emit(literal)
    require(next(lexical, None) is None and consumed == len(arg_values), "unconsumed content or arguments")
    require(len(output) == raw_size, "decoded size differs")
    return bytes(output)


def exact_read(source, count):
    data = source.read(count)
    require(len(data) == count, "truncated archive")
    return data


def encode_stream(source, target, size, mode="auto", frame_size=MAX_FRAME, config=Config()):
    config.validate()
    require(0 <= size <= MAX_RAW and 1 <= frame_size <= MAX_FRAME, "input or frame limit")
    count = (size + frame_size - 1) // frame_size
    target.write(HEADER.pack(MAGIC, frame_size, count, size))
    reports = []
    for index in range(count):
        raw = exact_read(source, min(frame_size, size - index * frame_size))
        data, report = encode_frame(raw, mode, config)
        target.write(data)
        reports.append(report)
    require(source.read(1) == b"", "input grew beyond bound")
    totals = {key: sum(r[key] for r in reports) for key in
              ("literal_definition_bytes", "structure_bytes", "content_bytes", "argument_reference_bytes", "exception_bytes", "framing_bytes", "complete_archive_bytes")}
    totals["framing_bytes"] += HEADER.size
    totals["complete_archive_bytes"] += HEADER.size
    return dict(totals, raw_bytes=size, frames=reports, requested_mode=mode, frame_size=frame_size,
                config=config.__dict__, backend="zlib9", zlib_version=zlib.ZLIB_RUNTIME_VERSION,
                accounting="Compressed section sizes including backend tables; structure includes phrase/template definitions. Package excluded.")


def decode_stream(source, target, max_output=MAX_RAW):
    magic, frame_size, count, total = HEADER.unpack(exact_read(source, HEADER.size))
    require(magic == MAGIC and 1 <= frame_size <= MAX_FRAME and total <= min(max_output, MAX_RAW), "archive header or output bound")
    require(count == (total + frame_size - 1) // frame_size, "frame count differs")
    archive_bytes = HEADER.size
    for index in range(count):
        fields = FRAME.unpack(exact_read(source, FRAME.size))
        raw_size, mode, *rest = fields
        lengths, expected_hash = rest[:5], rest[5]
        require(raw_size == min(frame_size, total - index * frame_size) and mode in MODES.values(), "frame identity differs")
        require(all(n <= 2 * MAX_SECTION for n in lengths), "compressed section bound")
        archive_bytes += FRAME.size + sum(lengths)
        require(archive_bytes <= MAX_ARCHIVE, "archive size bound")
        sections = [exact_read(source, n) for n in lengths]
        if mode == 0:
            require(all(not sections[i] for i in (0, 1, 2, 4)), "plain frame has extra streams")
            raw = inflate(sections[3])
        else:
            raw = interpret(sections, raw_size)
        require(len(raw) == raw_size and hashlib.sha256(raw).digest() == expected_hash, "raw checksum differs")
        target.write(raw)
    require(source.read(1) == b"", "trailing archive data")
    return dict(raw_bytes=total, complete_archive_bytes=archive_bytes, frames=count)


def encode(data, **kwargs):
    output = io.BytesIO()
    report = encode_stream(io.BytesIO(data), output, len(data), **kwargs)
    return output.getvalue(), report


def decode(data, max_output=MAX_RAW):
    require(len(data) <= MAX_ARCHIVE, "archive input bound")
    output = io.BytesIO()
    decode_stream(io.BytesIO(data), output, max_output)
    return output.getvalue()


def new_file(path, write):
    """Publish a closed new file without replacing any existing target."""
    path = Path(path)
    require(not path.exists(), "output target exists")
    name = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as target:
            name = target.name
            report = write(target)
            target.flush()
            os.fsync(target.fileno())
        os.link(name, path)
        return report
    finally:
        if name is not None:
            os.unlink(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("encode", "decode", "bench"))
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument("--mode", choices=(*MODES, "auto"), default="auto")
    parser.add_argument("--frame-size", type=int, default=MAX_FRAME)
    parser.add_argument("--max-rule-length", type=int, default=8)
    parser.add_argument("--grammar-budget", type=int, default=16)
    parser.add_argument("--min-benefit", type=int, default=1)
    args = parser.parse_args()
    config = Config(args.max_rule_length, args.grammar_budget, args.min_benefit)
    config.validate()
    begin, cpu = time.monotonic(), time.process_time()
    with args.input.open("rb") as source:
        if args.operation == "bench":
            raw = source.read(MAX_RAW + 1)
            require(len(raw) <= MAX_RAW, "input limit")
            report = {}
            for mode in MODES:
                archive, info = encode(raw, mode=mode, frame_size=args.frame_size, config=config)
                require(decode(archive) == raw, "benchmark inverse differs")
                repeat, _ = encode(raw, mode=mode, frame_size=args.frame_size, config=config)
                require(repeat == archive, "benchmark repeat differs")
                report[mode] = dict(info, exact_inverse=True, deterministic_repeat=True,
                                    archive_sha256=hashlib.sha256(archive).hexdigest())
        else:
            require(args.output is not None, "output path required")
            if args.operation == "encode":
                size = os.fstat(source.fileno()).st_size
                report = new_file(args.output, lambda target: encode_stream(source, target, size, args.mode, args.frame_size, config))
            else:
                report = new_file(args.output, lambda target: decode_stream(source, target))
    report = dict(result=report, cpu_seconds=time.process_time() - cpu, elapsed_seconds=time.monotonic() - begin,
                  peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  complete_package_bytes=None, full_corpus_score_bytes=None)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
