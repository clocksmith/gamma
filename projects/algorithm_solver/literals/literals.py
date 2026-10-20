"""Flat literal dictionaries: exact encoding, shortest segmentation, bounded mining.

No identifier binding, parameter substitution, grammar expansion, or free separators.
This operates offline on supplied source; it does not solve a problem description.
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
from collections import Counter, defaultdict


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_dictionary(literals: list[str]) -> None:
    if not isinstance(literals, list) or not literals:
        raise ValueError("nonempty literal list required")
    if any(not isinstance(item, str) or not item for item in literals):
        raise ValueError("empty or non-string literal")
    if len(set(literals)) != len(literals):
        raise ValueError("duplicate literal")
    for item in literals:
        item.encode("utf-8", errors="strict")


def reconstruct(literals: list[str], sequence: list[int]) -> str:
    validate_dictionary(literals)
    if not isinstance(sequence, list) or any(
        type(index) is not int or not 0 <= index < len(literals)
        for index in sequence
    ):
        raise ValueError("invalid literal ID")
    return "".join(literals[index] for index in sequence)


def shortest_encode(source: str, literals: list[str]) -> list[int]:
    """Exact DAG shortest path; each literal selection costs one.

    Ties use the smaller first literal ID, recursively. All characters participate.
    This is optimal segmentation of supplied text under a fixed dictionary only.
    """
    validate_dictionary(literals)
    by_first = defaultdict(list)
    for index, literal in enumerate(literals):
        by_first[literal[0]].append((index, literal))
    size = len(source)
    costs = [size + 1] * (size + 1)
    next_edges = [None] * size
    costs[size] = 0
    for position in range(size - 1, -1, -1):
        for index, literal in by_first[source[position]]:
            end = position + len(literal)
            if source.startswith(literal, position) and costs[end] + 1 < costs[position]:
                costs[position] = costs[end] + 1
                next_edges[position] = (index, end)
    if costs[0] > size:
        raise ValueError("source cannot be represented")
    sequence = []
    position = 0
    while position < size:
        index, position = next_edges[position]
        sequence.append(index)
    return sequence


def dictionary_bytes(literals: list[str]) -> bytes:
    validate_dictionary(literals)
    fields = [b"LTD1", struct.pack(">I", len(literals))]
    for literal in literals:
        raw = literal.encode("utf-8")
        fields.extend((struct.pack(">I", len(raw)), raw))
    return b"".join(fields)


def program_bytes(literals: list[str], sequence: list[int]) -> bytes:
    reconstruct(literals, sequence)
    return (
        b"LTP1"
        + hashlib.sha256(dictionary_bytes(literals)).digest()
        + struct.pack(">I", len(sequence))
        + b"".join(struct.pack(">I", index) for index in sequence)
    )


def program4_bytes(literals: list[str], sequence: list[int]) -> bytes:
    """Fixed four-bit selections, with zero low-nibble padding for odd length."""
    reconstruct(literals, sequence)
    if len(literals) > 16:
        raise ValueError("four-bit dictionary exceeds sixteen literals")
    payload = bytearray()
    for offset in range(0, len(sequence), 2):
        high = sequence[offset]
        low = sequence[offset + 1] if offset + 1 < len(sequence) else 0
        payload.append((high << 4) | low)
    return b"LT41" + hashlib.sha256(dictionary_bytes(literals)).digest() + struct.pack(">I", len(sequence)) + payload


def decode4_bytes(dictionary: bytes, program: bytes) -> str:
    if len(program) < 40 or program[:4] != b"LT41":
        raise ValueError("four-bit program header")
    count = struct.unpack_from(">I", program, 36)[0]
    if len(program) != 40 + (count + 1) // 2:
        raise ValueError("four-bit program length")
    if count % 2 and program[-1] & 15:
        raise ValueError("nonzero four-bit padding")
    if len(dictionary) < 8 or struct.unpack_from(">I", dictionary, 4)[0] > 16:
        raise ValueError("four-bit dictionary exceeds sixteen literals")
    sequence = [((program[40 + index // 2] >> (4 if index % 2 == 0 else 0)) & 15)
                for index in range(count)]
    expanded = b"LTP1" + program[4:40] + b"".join(struct.pack(">I", index) for index in sequence)
    return decode_bytes(dictionary, expanded)

def decode_bytes(dictionary: bytes, program: bytes) -> str:
    """Strict standalone decoder; rejects truncation, trailing data, wrong dictionary."""
    if dictionary[:4] != b"LTD1" or len(dictionary) < 8:
        raise ValueError("dictionary header")
    count = struct.unpack_from(">I", dictionary, 4)[0]
    position = 8
    literals = []
    for _ in range(count):
        if position + 4 > len(dictionary):
            raise ValueError("dictionary length")
        length = struct.unpack_from(">I", dictionary, position)[0]
        position += 4
        if position + length > len(dictionary):
            raise ValueError("dictionary truncation")
        literals.append(dictionary[position:position + length].decode("utf-8"))
        position += length
    if position != len(dictionary):
        raise ValueError("dictionary trailing data")
    validate_dictionary(literals)
    if len(program) < 40 or program[:4] != b"LTP1":
        raise ValueError("program header")
    if program[4:36] != hashlib.sha256(dictionary).digest():
        raise ValueError("dictionary mismatch")
    count = struct.unpack_from(">I", program, 36)[0]
    if len(program) != 40 + 4 * count:
        raise ValueError("program length")
    return reconstruct(literals, list(struct.unpack_from(f">{count}I", program, 40)))


def pieces(source: str, mode: str) -> list[str]:
    if mode == "characters":
        return list(source)
    if mode == "lines":
        return source.splitlines(keepends=True)
    if mode == "whole":
        return [source]
    if mode == "lexical":
        # A lossless splitter, not a JavaScript parser. Quoted strings and comments
        # may split; they are restored verbatim, never interpreted or rewritten.
        return re.findall(r"[A-Za-z_$][A-Za-z0-9_$]*|[0-9]+|\s+|.", source, re.DOTALL)
    raise ValueError(mode)


def merged_dictionary(sources: list[str], mode: str, steps: int, shared: bool) -> list[str]:
    """Deterministic adjacent-pair merging. Shared mode needs two distinct programs.

    Entries are stored as their full literal strings; no nonterminal references.
    Intermediate literals remain candidates; unused entries are pruned after DP.
    """
    streams = [pieces(source, mode) for source in sources]
    vocabulary = {item for stream in streams for item in stream}
    for _ in range(steps):
        counts = Counter()
        owners = defaultdict(set)
        for owner, stream in enumerate(streams):
            for pair in zip(stream, stream[1:]):
                counts[pair] += 1
                owners[pair].add(owner)
        eligible = [pair for pair, count in counts.items()
                    if count >= 2 and (not shared or len(owners[pair]) >= 2)]
        if not eligible:
            break
        # Ranking is the declared merge heuristic, not a hidden final objective.
        pair = min(eligible, key=lambda p: (-counts[p], p))
        merged = "".join(pair)
        vocabulary.add(merged)
        for owner, stream in enumerate(streams):
            result = []
            position = 0
            while position < len(stream):
                if tuple(stream[position:position + 2]) == pair:
                    result.append(merged)
                    position += 2
                else:
                    result.append(stream[position])
                    position += 1
            streams[owner] = result
    return sorted(vocabulary)


def encode_corpus(sources: dict[str, str], vocabulary: list[str]) -> dict:
    sequences = {key: shortest_encode(source, vocabulary) for key, source in sources.items()}
    used = sorted({index for seq in sequences.values() for index in seq})
    literals = [vocabulary[index] for index in used]
    remap = {old: new for new, old in enumerate(used)}
    sequences = {key: [remap[index] for index in seq] for key, seq in sequences.items()}
    packed_dictionary = dictionary_bytes(literals)
    programs = {}
    owner_counts = Counter()
    for key, source in sources.items():
        sequence = sequences[key]
        packed = program_bytes(literals, sequence)
        if decode_bytes(packed_dictionary, packed) != source:
            raise RuntimeError("reconstruction mismatch")
        owner_counts.update(set(sequence))
        programs[key] = {
            "sequence": sequence, "source_sha256": digest(source.encode()),
            "source_utf8_bytes": len(source.encode()), "selections": len(sequence),
            "encoded_bytes": len(packed), "encoded_sha256": digest(packed),
        }
    lengths = sorted(len(seq) for seq in sequences.values())
    count = len(lengths)
    median = (lengths[(count - 1) // 2] + lengths[count // 2]) / 2
    return {
        "schema": "gamma.literal-encoding.v1",
        "format": "LTD1 dictionary / LTP1 programs; direct UTF-8 concatenation",
        "literals": literals, "programs": programs,
        "metrics": {
            "vocabulary_cardinality": len(literals),
            "literal_utf8_bytes": sum(len(s.encode()) for s in literals),
            "dictionary_bytes": len(packed_dictionary),
            "total_selections": sum(lengths), "median_selections": median,
            "worst_selections": max(lengths),
            "program_bytes": sum(row["encoded_bytes"] for row in programs.values()),
            "package_bytes": len(packed_dictionary) + sum(row["encoded_bytes"] for row in programs.values()),
            "cross_program_literals": sum(owners >= 2 for owners in owner_counts.values()),
            "cross_program_selections": sum(
                owner_counts[index] >= 2 for seq in sequences.values() for index in seq
            ),
            "exact_reconstructions": count,
            "four_bit_feasible": len(literals) <= 16,
            "four_bit_selection_bits": 4 * sum(lengths) if len(literals) <= 16 else None,
            "four_bit_framing_bytes": 40 * count if len(literals) <= 16 else None,
            "four_bit_payload_bytes": sum((size + 1) // 2 for size in lengths) if len(literals) <= 16 else None,
        },
    }


OBJECTIVES = ("vocabulary_cardinality", "dictionary_bytes", "total_selections")


def dominates(left: dict, right: dict) -> bool:
    a, b = left["metrics"], right["metrics"]
    return all(a[key] <= b[key] for key in OBJECTIVES) and any(
        a[key] < b[key] for key in OBJECTIVES
    )


def pareto(rows: list[dict]) -> list[dict]:
    return [row for row in rows if not any(dominates(other, row) for other in rows)]


def json_bytes(value) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
