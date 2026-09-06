#!/usr/bin/env python3
"""D2GRAM02: supply exact template arguments through the shared token pool.

This explicit format adapter reuses the sealed v1 discovery and interpreter in
an isolated module. It changes argument representation only. The v1 file and
ordinary imports remain unchanged; both sources are required package inputs.
Whole arguments no longer become dictionary literals. Each argument transmits
a token count followed by literal-token references, including exact separators.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


CORE_PATH = Path(__file__).with_name("dualstream_grammar_v1.py")
spec = importlib.util.spec_from_file_location(__name__ + "_core", CORE_PATH)
core = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = core
spec.loader.exec_module(core)
core.MAGIC = b"D2GRAM02"
original_pack = core.packed_sections
original_interpret = core.interpret


def pack_arguments(model):
    """Intern argument tokens after ordinary content, preserving other IDs."""
    tokenized = [tuple(core.tokenize(value)) for value in model.arguments]
    tokens = tuple(token for argument in tokenized for token in argument)
    augmented = core.replace(model, arguments=(), content=model.content + tokens)
    sections = list(original_pack(augmented))
    reader = core.Reader(core.inflate(sections[3]))
    count = reader.number(2 * core.MAX_FRAME)
    core.require(count == len(augmented.content), "augmented token count differs")
    codes = [reader.number() for _ in range(count)]
    reader.end()
    ordinary = codes[:len(model.content)]
    arguments = bytearray(core.uint(len(tokenized)))
    index = len(ordinary)
    for argument in tokenized:
        selected = codes[index:index + len(argument)]
        core.require(all(code & 1 == 0 for code in selected), "argument token must be literal")
        arguments.extend(core.uint(len(argument)))
        arguments.extend(b"".join(core.uint(code) for code in selected))
        index += len(argument)
    core.require(index == len(codes), "unconsumed argument tokens")
    content = core.uint(len(ordinary)) + b"".join(core.uint(code) for code in ordinary)
    core.require(len(arguments) <= core.MAX_SECTION, "argument section limit")
    sections[3] = core.zlib.compress(content, 9)
    sections[4] = core.zlib.compress(bytes(arguments), 9)
    return tuple(sections)


def interpret_arguments(sections, raw_size):
    """Reconstruct bounded arguments, then reuse the unchanged exact interpreter."""
    reader = core.Reader(core.inflate(sections[0]))
    pool = [reader.take(reader.number(core.MAX_SECTION))
            for _ in range(reader.number(2 * core.MAX_FRAME))]
    reader.end()
    tokens = core.Reader(core.inflate(sections[4]))
    arguments, expanded, token_count = [], 0, 0
    for _ in range(tokens.number(2 * core.MAX_FRAME)):
        count = tokens.number(2 * core.MAX_FRAME)
        token_count += count
        core.require(token_count <= 2 * core.MAX_FRAME, "argument token work limit")
        argument = bytearray()
        for _ in range(count):
            code = tokens.number()
            core.require(code & 1 == 0 and code >> 1 < len(pool), "invalid argument token reference")
            token = pool[code >> 1]
            core.require(len(argument) + len(token) <= raw_size, "argument expansion limit")
            argument.extend(token)
        expanded += len(argument)
        core.require(expanded <= core.MAX_SECTION, "total argument expansion limit")
        arguments.append(bytes(argument))
    tokens.end()
    ids = {value: index for index, value in enumerate(pool)}
    references = []
    for argument in arguments:
        if argument not in ids:
            ids[argument] = len(pool)
            pool.append(argument)
        references.append(ids[argument])
    definitions = core.uint(len(pool)) + b"".join(core.uint(len(value)) + value for value in pool)
    core.require(len(pool) <= 2 * core.MAX_FRAME and len(definitions) <= core.MAX_SECTION,
                 "expanded dictionary limit")
    legacy_arguments = core.uint(len(references)) + b"".join(core.uint(index) for index in references)
    adapted = list(sections)
    adapted[0] = core.zlib.compress(definitions, 9)
    adapted[4] = core.zlib.compress(legacy_arguments, 9)
    return original_interpret(adapted, raw_size)


core.packed_sections = pack_arguments
core.interpret = interpret_arguments


def __getattr__(name):
    return getattr(core, name)


if __name__ == "__main__":
    core.main()
