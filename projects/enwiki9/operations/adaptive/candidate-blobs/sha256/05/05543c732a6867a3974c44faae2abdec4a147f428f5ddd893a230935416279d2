#!/usr/bin/env python3
"""Reserialize fixed D2GRAM01/02 programs; do not rediscover a grammar.

Both immutable codec sources are dependencies. The existing decoders validate
inputs first; a tagged graph bridges their distinct private Python classes.
Archive repeats from this tool prove deterministic program serialization only.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import dualstream_grammar_v1 as old
from tools import dualstream_grammar_argtokens_v2 as new

VERSIONS = {"old": old, "new": new}
FIELDS = ("structure", "content", "arguments", "phrases", "templates", "structure_rules")
COSTS = ("literal_definition_bytes", "structure_bytes", "content_bytes",
         "argument_reference_bytes", "exception_bytes", "framing_bytes", "complete_archive_bytes")
require = old.require


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tagged(value):
    if isinstance(value, bytes):
        return ["bytes", value.hex()]
    if isinstance(value, (old.Ref, new.Ref)):
        return ["ref", value.index]
    if isinstance(value, (old.Arg, new.Arg)):
        return ["arg", value.index]
    if isinstance(value, tuple):
        return ["tuple", [tagged(item) for item in value]]
    require(type(value) in (int, str), "unknown program value")
    return [type(value).__name__, value]


def untagged(value, codec):
    kind, body = value
    if kind == "bytes":
        return bytes.fromhex(body)
    if kind == "ref":
        return codec.Ref(body)
    if kind == "arg":
        return codec.Arg(body)
    if kind == "tuple":
        return tuple(untagged(item, codec) for item in body)
    require(kind in ("int", "str"), "unknown program tag")
    return body


def graph(model):
    return {field: tagged(getattr(model, field)) for field in FIELDS}


def fingerprint(model):
    return sha(json.dumps(graph(model), sort_keys=True, separators=(",", ":")).encode())


def convert(model, codec):
    before = graph(model)
    converted = codec.Model(**{field: untagged(before[field], codec) for field in FIELDS})
    require(graph(converted) == before, "native class adapter changed program")
    return converted


def unpack_model(sections, raw_size, version):
    """Read the transmitted graph after its authoritative interpreter validates it."""
    codec = VERSIONS[version]
    codec.interpret(sections, raw_size)
    pool_reader, programs, structure, content, arguments = [old.Reader(old.inflate(s)) for s in sections]
    pool = [pool_reader.take(pool_reader.number(old.MAX_SECTION))
            for _ in range(pool_reader.number(2 * old.MAX_FRAME))]
    pool_reader.end()

    def cp(code):
        return old.Ref(code >> 1) if code & 1 else pool[code >> 1]

    def sp(code):
        index, kind = code >> 2, code & 3
        if kind == 0:
            return ("literal", pool[index])
        if kind == 1:
            return ("content", index + 1)
        if kind == 2:
            return ("call", index)
        return old.Ref(index)

    phrases = tuple(tuple(cp(programs.number()) for _ in range(2))
                    for _ in range(programs.number(64)))
    templates = []
    for _ in range(programs.number(64)):
        arity, length = programs.number(32), programs.number(2 * old.MAX_FRAME)
        body = []
        for _ in range(length):
            code = programs.number()
            body.append(old.Arg(code >> 1) if code & 1 else cp(code >> 1))
        templates.append((arity, tuple(body)))
    structure_rules = tuple(tuple(sp(programs.number()) for _ in range(2))
                            for _ in range(programs.number(64)))
    programs.end()
    roots = tuple(sp(structure.number()) for _ in range(structure.number(2 * old.MAX_FRAME)))
    structure.end()
    words = tuple(cp(content.number()) for _ in range(content.number(2 * old.MAX_FRAME)))
    content.end()
    supplied = []
    for _ in range(arguments.number(2 * old.MAX_FRAME)):
        if version == "old":
            supplied.append(pool[arguments.number()])
        else:
            tokens = [arguments.number() for _ in range(arguments.number(2 * old.MAX_FRAME))]
            require(all(code & 1 == 0 for code in tokens), "nonliteral argument token")
            supplied.append(b"".join(pool[code >> 1] for code in tokens))
    arguments.end()
    return old.Model(roots, words, tuple(supplied), phrases, tuple(templates), structure_rules)


def repeated_bindings(model):
    calls, stack, work = Counter(), list(model.structure), 0
    while stack:
        work += 1
        require(work <= 16 * old.MAX_FRAME, "structure work bound")
        value = stack.pop()
        if isinstance(value, old.Ref):
            stack.extend(model.structure_rules[value.index])
        elif value[0] == "call":
            calls[value[1]] += 1
    return sum(calls[index] * (sum(isinstance(x, old.Arg) for x in body) - arity)
               for index, (arity, body) in enumerate(model.templates))


def split_frame(encoded):
    fields = old.FRAME.unpack(encoded[:old.FRAME.size])
    reader = old.Reader(encoded[old.FRAME.size:])
    sections = tuple(reader.take(n) for n in fields[2:7])
    reader.end()
    return sections


def reserialize(archive, storage):
    require(storage in VERSIONS and len(archive) <= old.MAX_ARCHIVE, "storage or archive bound")
    source_version = next((name for name, codec in VERSIONS.items() if archive[:8] == codec.MAGIC), None)
    require(source_version is not None, "unknown archive version")
    source_codec, target_codec = VERSIONS[source_version], VERSIONS[storage]
    raw = source_codec.decode(archive)
    reader = old.Reader(archive)
    _, frame_size, count, total = old.HEADER.unpack(reader.take(old.HEADER.size))
    output = bytearray(old.HEADER.pack(target_codec.MAGIC, frame_size, count, total))
    reports, offset = [], 0
    for _ in range(count):
        fields = old.FRAME.unpack(reader.take(old.FRAME.size))
        raw_size, mode_id = fields[:2]
        sections = tuple(reader.take(n) for n in fields[2:7])
        part = raw[offset:offset + raw_size]
        mode = next(name for name, value in old.MODES.items() if value == mode_id)
        model = old.Model() if mode == "plain" else unpack_model(sections, raw_size, source_version)
        equivalent = convert(model, target_codec)
        encoded, costs = target_codec.frame_bytes(part, mode, equivalent)
        fixed_sections = split_frame(encoded)
        require(all(sections[i] == fixed_sections[i] for i in (1, 2, 3)), "fixed section changed")
        recovered = old.Model() if mode == "plain" else unpack_model(fixed_sections, raw_size, storage)
        require(graph(model) == graph(recovered), "reserialized program changed")
        require(len(output) + len(encoded) <= old.MAX_ARCHIVE, "archive size bound")
        output.extend(encoded)
        reports.append(dict(costs, raw_bytes=raw_size, raw_offset=offset, raw_sha256=sha(part), mode=mode,
                            model_sha256=fingerprint(model), supplied_arguments=len(model.arguments),
                            templates=len(model.templates), repeated_argument_references=repeated_bindings(model),
                            fixed_sections_sha256={key: sha(sections[index])
                                for index, key in ((1, "programs"), (2, "structure"), (3, "content"))}))
        offset += raw_size
    reader.end()
    require(offset == total and target_codec.decode(bytes(output)) == raw, "reserialized inverse differs")
    if storage == source_version:
        require(bytes(output) == archive, "diagonal archive identity differs")
    totals = {key: sum(report[key] for report in reports) for key in COSTS}
    totals["framing_bytes"] += old.HEADER.size
    totals["complete_archive_bytes"] += old.HEADER.size
    require(totals["complete_archive_bytes"] == len(output), "archive accounting differs")
    report = dict(totals, raw_bytes=total, raw_sha256=sha(raw), frames=reports, frame_size=frame_size,
                  selection_version=source_version, storage_version=storage, input_archive_sha256=sha(archive),
                  program_identity_pass=True, fixed_sections_pass=True,
                  repeat_scope="fixed-program-reserialization", raw_encoder_repeat_proved=False,
                  backend="zlib9", zlib_version=old.zlib.ZLIB_RUNTIME_VERSION,
                  accounting="Every transmitted section and header counted. Complete decoder package excluded.")
    return bytes(output), report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("encode",))
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--storage", required=True, choices=tuple(VERSIONS))
    args = parser.parse_args()
    begin, cpu = time.monotonic(), time.process_time()
    with args.input.open("rb") as source:
        archive = source.read(old.MAX_ARCHIVE + 1)
    encoded, result = reserialize(archive, args.storage)
    def write(target):
        target.write(encoded)
        return result
    old.new_file(args.output, write)
    print(json.dumps(dict(result=result, cpu_seconds=time.process_time() - cpu,
                         elapsed_seconds=time.monotonic() - begin,
                         peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                         complete_package_bytes=None, full_corpus_score_bytes=None), sort_keys=True))


if __name__ == "__main__":
    main()
