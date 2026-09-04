#!/usr/bin/env python3
"""Independent generated fixture for HARM-Delta scope-coordinate mapping."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
from typing import Any, Callable


STORE_WRAPPER = bytes((0x80, 0, 0, 0, 0))
RAW = b"alphabeta" + b"gamma" + b"Alpha" + b"ALPHA" + b"!" + b"{{t|k=delta}}"
RAW_BOUNDARIES = (0, 7, 14, 21, 25, 30, 38)
EXPECTED_WRT_BOUNDARIES = (0, 9, 12, 16, 19, 24, 32)
FNV_OFFSET = 1469598103934665603
FNV_PRIME = 1099511628211
MASK64 = (1 << 64) - 1
STATE_DOMAIN = b"HARM-FRONTEND-STATE-v1\0"

FROZEN_BINDINGS = {
    "static_contract": (
        "operations/planning/harm_delta_scope_coordinate_mapper_q0_v1.json",
        "30ef264c5e63551222709e0611bfe92c61b6c5fa758be86dfdc7a3f7f7bd03fd",
    ),
    "semantic_route_revision": (
        "operations/adaptive/candidate-revisions/endpoint428_semantic_route_tape_q0_v3/20260901T131904564070Z_c0f355845c3b.json",
        "031036a3f62bee9adaab1a88c2070ea71c66c8bc900b67e2b1b033f338d0bb58",
    ),
    "semantic_route_native_inverse": (
        "programs/endpoint428_semantic_route_tape_q0_v3/semantic-route-tape.cpp",
        "b44fffb2b95c540535d293e1d0021f544a5b7e4d8fbb740721752a69b0c7866e",
    ),
    "semantic_route_independent_inverse": (
        "programs/endpoint428_semantic_route_tape_q0_v3/semantic-replay.cpp",
        "65c348393c438f812ca5b497dfd5f545ffefbbe3d4b3113a553507098495e3b7",
    ),
    "semantic_route_fixture_builder": (
        "programs/endpoint428_semantic_route_tape_q0_v3/build_fixture.py",
        "cb522cbbd29fe3c8e4a7bcb212a09ef81018cd02b0612efa5e42c1bc083791db",
    ),
}


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _forward_remap(value: int) -> int:
    """The Endpoint428 remap is an involution; apply it to encode a literal."""
    if ord("{") <= value < 127:
        value += ord("P") - ord("{")
    elif ord("P") <= value < ord("T"):
        value += ord("{") - ord("P")
    elif ord(":") <= value <= ord("?") or ord("J") <= value <= ord("O"):
        value ^= 0x70
    if value in (ord("X"), ord("`")):
        value ^= ord("X") ^ ord("`")
    return value


def fixture_dictionary() -> bytes:
    words = [b"a"] * 3921
    words[0] = b"alpha"
    words[80] = b"beta"
    words[3920] = b"gamma"
    return b"".join(word + b"\n" for word in words)


def fixture_wrt() -> bytes:
    header = bytes((7, 0, 0, 0, len(RAW), 7))
    payload = bytes((
        0x80,
        0xD0, 0x80,
        0xF0, 0xD0, 0x80,
        0x40, 0x80,
        0x07, 0x80, 0x06,
        0x0C, _forward_remap(ord("!")),
    )) + bytes(_forward_remap(value) for value in b"{{t|k=delta}}")
    wrt = header + payload
    if len(wrt) != 32:
        raise AssertionError("fixture WRT geometry differs")
    return wrt


def fixture_store() -> bytes:
    return STORE_WRAPPER + fixture_wrt()


def _dictionary_codes(data: bytes) -> tuple[dict[int, bytes], int]:
    reverse: dict[int, bytes] = {}
    word = bytearray()
    line = 0
    for value in data:
        if ord("a") <= value <= ord("z"):
            word.append(value)
            continue
        if not word:
            continue
        if line < 80:
            code = 0x80 + line
        elif line < 3920:
            code = 0xD0 + (line - 80) // 80
            code |= (0x80 + (line - 80) % 80) << 8
        elif line < 44880:
            code = 0xF0 + ((line - 3920) // 80) // 32
            code |= (0xD0 + ((line - 3920) // 80) % 32) << 8
            code |= (0x80 + (line - 3920) % 80) << 16
        else:
            raise AssertionError("reference dictionary line bound")
        reverse[code] = bytes(word)
        word.clear()
        line += 1
    if word:
        raise AssertionError("reference dictionary terminator differs")
    if line != 3921:
        raise AssertionError("reference dictionary word count differs")
    return reverse, line


def _fnv_byte(state: int, value: int) -> int:
    return ((state ^ value) * FNV_PRIME) & MASK64


def _state_digest(
    coordinate: int,
    raw_position: int,
    raw_length_header: int,
    raw_fnv: int,
    wrt_fnv: int,
    code: int,
    code_bytes: int,
    code_needed: int,
    dictionary_words: int,
    uppercase: bool,
    capitalized: bool,
    pending_escape: bool,
) -> str:
    state = struct.pack(
        "<5Q4I4B",
        coordinate,
        raw_position,
        raw_length_header,
        raw_fnv,
        wrt_fnv,
        code,
        code_bytes,
        code_needed,
        dictionary_words,
        uppercase,
        capitalized,
        pending_escape,
        0,
    )
    return hashlib.sha256(STATE_DOMAIN + state).hexdigest()


def reference_evidence(store: bytes, raw: bytes, dictionary: bytes) -> tuple[dict[str, Any], list[tuple[int, int, int]]]:
    if store[:5] != STORE_WRAPPER:
        raise AssertionError("reference wrapper differs")
    wrt = store[5:]
    reverse, dictionary_words = _dictionary_codes(dictionary)
    raw_position = 0
    raw_length_header = 0
    raw_fnv = FNV_OFFSET
    wrt_fnv = FNV_OFFSET
    uppercase = False
    capitalized = False
    pending_escape = False
    code = 0
    code_bytes = 0
    code_needed = 0
    next_boundary = 0
    boundaries: list[dict[str, Any]] = []
    transcript: list[tuple[int, int, int]] = []

    def emit(value: int) -> None:
        nonlocal raw_position, raw_fnv
        if raw_position >= len(raw) or raw[raw_position] != value:
            raise AssertionError("reference raw identity differs")
        raw_fnv = _fnv_byte(raw_fnv, value)
        raw_position += 1

    def emit_word(candidate: int) -> None:
        nonlocal capitalized
        word = reverse.get(candidate)
        if word is None:
            raise AssertionError("reference dictionary code differs")
        for index, item in enumerate(word):
            value = item
            if index == 0 and capitalized:
                value = value - ord("a") + ord("A")
                capitalized = False
            if uppercase:
                value = value - ord("a") + ord("A")
            emit(value)

    def capture(coordinate: int) -> None:
        nonlocal next_boundary
        while next_boundary < len(RAW_BOUNDARIES) and raw_position >= RAW_BOUNDARIES[next_boundary]:
            raw_boundary = RAW_BOUNDARIES[next_boundary]
            boundaries.append(
                {
                    "rawBoundary": raw_boundary,
                    "wrtCoordinate": coordinate,
                    "coderBitCoordinate": coordinate * 8,
                    "rawBefore": raw_position,
                    "frontendStateSha256": _state_digest(
                        coordinate,
                        raw_position,
                        raw_length_header,
                        raw_fnv,
                        wrt_fnv,
                        code,
                        code_bytes,
                        code_needed,
                        dictionary_words,
                        uppercase,
                        capitalized,
                        pending_escape,
                    ),
                }
            )
            next_boundary += 1

    for coordinate, stored in enumerate(wrt):
        capture(coordinate)
        before = raw_position
        wrt_fnv = _fnv_byte(wrt_fnv, stored)
        if coordinate < 5:
            if coordinate == 0 and stored != 7:
                raise AssertionError("reference WRT type differs")
            if coordinate:
                raw_length_header = (raw_length_header << 8) | stored
        elif coordinate == 5:
            if stored != 7:
                raise AssertionError("reference WRT marker differs")
        else:
            value = _forward_remap(stored)
            if pending_escape:
                uppercase = False
                pending_escape = False
                emit(value)
            elif code_needed:
                code |= value << (8 * code_bytes)
                code_bytes += 1
                code_needed -= 1
                if code_bytes == 2 and value > 0xCF:
                    code_needed += 1
                if code_needed == 0:
                    emit_word(code)
                    code = 0
                    code_bytes = 0
            elif value == 0x0C:
                pending_escape = True
            elif value == 0x07:
                uppercase = True
            elif value == 0x40:
                capitalized = True
            elif value == 0x06:
                uppercase = False
            elif value >= 0x80:
                code = value
                code_bytes = 1
                code_needed = int(value > 0xCF)
                if code_needed == 0:
                    emit_word(code)
                    code = 0
                    code_bytes = 0
            else:
                literal = value
                alphabetic = ord("a") <= literal <= ord("z") or ord("A") <= literal <= ord("Z")
                if not alphabetic:
                    uppercase = False
                if capitalized or uppercase:
                    literal = literal - ord("a") + ord("A")
                if capitalized:
                    capitalized = False
                emit(literal)
        transcript.append((coordinate, before, raw_position))

    if pending_escape or code_needed or code_bytes or code:
        raise AssertionError("reference terminal code differs")
    if raw_length_header != len(raw) or raw_position != len(raw):
        raise AssertionError("reference raw length differs")
    capture(len(wrt))
    if next_boundary != len(RAW_BOUNDARIES):
        raise AssertionError("reference boundary closure differs")

    transcript_payload = b"".join(struct.pack("<3Q", *row) for row in transcript)
    by_raw = {row["rawBoundary"]: row for row in boundaries}

    def scope(raw_begin: int, raw_end: int) -> dict[str, int]:
        wrt_begin = by_raw[raw_begin]["wrtCoordinate"]
        wrt_end = by_raw[raw_end]["wrtCoordinate"]
        return {
            "rawBegin": raw_begin,
            "rawEnd": raw_end,
            "wrtBegin": wrt_begin,
            "wrtEnd": wrt_end,
            "coderBitBegin": wrt_begin * 8,
            "coderBitEnd": wrt_end * 8,
        }

    evidence = {
        "schema": "gamma.enwiki9.harm-delta-scope-coordinate-map-fixture.v1",
        "mode": "fixture",
        "storeBytes": len(store),
        "storeWrapperBytes": len(STORE_WRAPPER),
        "wrtBytes": len(wrt),
        "rawBytes": len(raw),
        "dictionaryBytes": len(dictionary),
        "dictionaryWords": dictionary_words,
        "inputSha256": {
            "store": hashlib.sha256(store).hexdigest(),
            "wrt": hashlib.sha256(wrt).hexdigest(),
            "raw": hashlib.sha256(raw).hexdigest(),
            "dictionary": hashlib.sha256(dictionary).hexdigest(),
        },
        "mappingTranscriptSha256": hashlib.sha256(transcript_payload).hexdigest(),
        "terminal": {
            "rawLengthHeader": raw_length_header,
            "rawPosition": raw_position,
            "rawFnv64": f"{raw_fnv:016x}",
            "wrtFnv64": f"{wrt_fnv:016x}",
        },
        "boundaries": boundaries,
        "scopes": {
            "opening": scope(0, 14),
            "distant": scope(21, 30),
        },
        "corpusAccessCount": 0,
        "activeTraceAccessCount": 0,
        "authority": {
            "archiveAuthority": False,
            "nativeIntegrationAuthority": False,
            "retainedParentGainAuthority": False,
            "corpusExecutionAuthority": False,
            "objectiveCreditBytes": 0,
        },
    }
    return evidence, transcript


def _run(command: list[str], *, expect_success: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if expect_success and completed.returncode != 0:
        raise RuntimeError(f"native command failed: {completed.stderr.strip()}")
    return completed


def build_native(source: Path, binary: Path, compiler: Path) -> list[str]:
    flags = [
        "-std=c++17",
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-pedantic",
        "-fno-fast-math",
        "-ffp-contract=off",
        "-march=x86-64",
        "-mtune=generic",
        "-Wl,--build-id=none",
    ]
    _run([str(compiler), *flags, str(source), "-o", str(binary)])
    return flags


def _write_inputs(root: Path, store: bytes, raw: bytes, dictionary: bytes) -> tuple[Path, Path, Path]:
    root.mkdir()
    store_path = root / "fixture.store"
    raw_path = root / "fixture.raw"
    dictionary_path = root / "fixture.dic"
    store_path.write_bytes(store)
    raw_path.write_bytes(raw)
    dictionary_path.write_bytes(dictionary)
    return store_path, raw_path, dictionary_path


def negative_controls(binary: Path, base: Path, root: Path) -> dict[str, str]:
    root.mkdir()
    rejected: dict[str, str] = {}

    def expect(label: str, mutation: Callable[[Path, Path, Path], None]) -> None:
        case = root / label
        case.mkdir()
        store = case / "fixture.store"
        raw = case / "fixture.raw"
        dictionary = case / "fixture.dic"
        shutil.copyfile(base / "fixture.store", store)
        shutil.copyfile(base / "fixture.raw", raw)
        shutil.copyfile(base / "fixture.dic", dictionary)
        mutation(store, raw, dictionary)
        output = case / "unexpected.json"
        completed = _run(
            [str(binary), "--fixture", str(store), str(raw), str(dictionary), str(output)],
            expect_success=False,
        )
        if completed.returncode == 0 or output.exists():
            raise AssertionError(f"negative control escaped or emitted output: {label}")
        rejected[label] = completed.stderr.strip()

    def symlink(path: Path) -> None:
        target = path.with_name(path.name + ".target")
        path.rename(target)
        path.symlink_to(target.name)

    expect("store_symlink", lambda store, _raw, _dictionary: symlink(store))
    expect("raw_symlink", lambda _store, raw, _dictionary: symlink(raw))
    expect("dictionary_symlink", lambda _store, _raw, dictionary: symlink(dictionary))

    def mutate(path: Path, offset: int, value: int) -> None:
        data = bytearray(path.read_bytes())
        data[offset] = value
        path.write_bytes(data)

    expect("store_wrapper_drift", lambda store, _raw, _dictionary: mutate(store, 0, 0x81))
    expect("raw_truth_mismatch", lambda _store, raw, _dictionary: mutate(raw, 0, ord("z")))
    expect("raw_length_header_mismatch", lambda store, _raw, _dictionary: mutate(store, 9, 39))
    expect("incomplete_terminal_dictionary_code", lambda store, _raw, _dictionary: mutate(store, len(fixture_store()) - 1, 0xD0))

    def dictionary_count(_store: Path, _raw: Path, dictionary: Path) -> None:
        data = dictionary.read_bytes()
        if not data.endswith(b"gamma\n"):
            raise AssertionError("fixture dictionary suffix differs")
        dictionary.write_bytes(data[: -len(b"gamma\n")])

    expect("dictionary_word_count_drift", dictionary_count)
    return rejected


def production_expected() -> dict[str, Any]:
    return {
        "schema": "gamma.enwiki9.harm-delta-scope-coordinate-map-production-description.v1",
        "mode": "production-description",
        "storeBytes": 647798597,
        "storeWrapperBytes": 5,
        "wrtBytes": 647798592,
        "rawBytes": 1_000_000_000,
        "dictionaryBytes": 411996,
        "inputSha256": {
            "store": "fe6ab5b96ad7bf2b6f7bd9f7cd3b3212ffc7320ae290e098f68e97b53295ceb9",
            "raw": "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc",
            "dictionary": "4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a",
        },
        "rawBoundaries": [0, 1_000_000, 500_000_000, 510_000_000, 1_000_000_000],
        "rawScopes": {
            "opening": [0, 1_000_000],
            "distant": [500_000_000, 510_000_000],
        },
        "boundaryLaw": "minimum-causal-wrt-coordinate-with-raw-before-greater-than-or-equal-to-raw-boundary",
        "coderOrder": "eight-msb-first-bits-per-wrt-byte",
        "productionExecutionExposed": False,
        "objectiveCreditBytes": 0,
    }


def _lower_bound_pass(rows: list[dict[str, Any]], transcript: list[tuple[int, int, int]]) -> bool:
    if tuple(row["wrtCoordinate"] for row in rows) != EXPECTED_WRT_BOUNDARIES:
        return False
    raw_before = [before for _coordinate, before, _after in transcript] + [len(RAW)]
    for boundary, row in zip(RAW_BOUNDARIES, rows, strict=True):
        coordinate = row["wrtCoordinate"]
        if raw_before[coordinate] < boundary:
            return False
        if coordinate and any(value >= boundary for value in raw_before[:coordinate]):
            return False
    return True


def run_fixture(project_root: Path, root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).resolve().parent / "scope-coordinate-mapper.cpp"
    compiler = Path("/usr/bin/x86_64-linux-gnu-g++-15")
    binding_receipts: dict[str, dict[str, str]] = {}
    for name, (relative, expected) in FROZEN_BINDINGS.items():
        path = project_root / relative
        actual = sha256_path(path)
        if actual != expected:
            raise AssertionError(f"{name} frozen binding differs")
        binding_receipts[name] = {"path": relative, "sha256": actual}

    binary = root / "scope-coordinate-mapper"
    flags = build_native(source, binary, compiler)
    store = fixture_store()
    dictionary = fixture_dictionary()
    if len(RAW) != 38 or len(store) != 37 or len(dictionary.splitlines()) != 3921:
        raise AssertionError("fixture geometry differs")

    paths_a = _write_inputs(root / "inputs-a", store, RAW, dictionary)
    paths_b = _write_inputs(root / "inputs-b", store, RAW, dictionary)
    output_a = root / "mapping-a.json"
    output_b = root / "mapping-b.json"
    _run([str(binary), "--fixture", *(str(path) for path in paths_a), str(output_a)])
    _run([str(binary), "--fixture", *(str(path) for path in paths_b), str(output_b)])
    native_a = json.loads(output_a.read_text(encoding="utf-8"))
    native_b = json.loads(output_b.read_text(encoding="utf-8"))
    expected, transcript = reference_evidence(store, RAW, dictionary)

    production_path = root / "production-description.json"
    _run([str(binary), "--describe-production", str(production_path)])
    production = json.loads(production_path.read_text(encoding="utf-8"))
    rejected = negative_controls(binary, root / "inputs-a", root / "negative")
    repeat_pass = output_a.read_bytes() == output_b.read_bytes() and native_a == native_b
    native_reference_pass = native_a == expected
    boundary_pass = _lower_bound_pass(expected["boundaries"], transcript)
    state_pass = [row["frontendStateSha256"] for row in native_a["boundaries"]] == [
        row["frontendStateSha256"] for row in expected["boundaries"]
    ]
    transcript_pass = native_a["mappingTranscriptSha256"] == expected["mappingTranscriptSha256"]
    production_pass = production == production_expected()

    return {
        "compile_flags": flags,
        "compiler_sha256": sha256_path(compiler),
        "source_sha256": sha256_path(source),
        "frozen_bindings": binding_receipts,
        "fixture_input_sha256": expected["inputSha256"],
        "native_reference_identity_pass": native_reference_pass,
        "repeat_identity_pass": repeat_pass,
        "boundary_lower_bound_pass": boundary_pass,
        "frontend_state_digest_pass": state_pass,
        "mapping_transcript_digest_pass": transcript_pass,
        "production_config_closure_pass": production_pass,
        "boundary_count": len(native_a["boundaries"]),
        "native_evidence": native_a,
        "reference_evidence": expected,
        "production_description": production,
        "negative_control_reject_count": len(rejected),
        "negative_control_rejections": rejected,
        "corpus_access_count": 0,
        "active_trace_access_count": 0,
        "opened_fixture_inputs": [str(path.resolve()) for path in (*paths_a, *paths_b, source)],
        "archive_authority": False,
        "retained_parent_gain_authority": False,
        "native_integration_authority": False,
        "corpus_execution_authority": False,
        "objective_credit_bytes": 0,
    }
