"""Qualified-source, deterministic flat-literal comparison. No source execution.

The command-line runner refuses to fit until its frozen source identities have a
fresh successful qualification receipt. Unit tests use inert synthetic text.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import statistics
import sys
import time

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
ALPHABET = [chr(i) for i in range(32, 127)] + ["\n"]
POLICY_FILE = LIT / "lagrange-select-v2" / "selection.py"
CODEC_FILE = LIT / "readable-v1" / "literal_codec.py"
SCORER_FILE = LIT / "literals.py"
VARIANTS = ("original", "shared-breadth")
LANGUAGES = ("javascript", "python")
PROBLEMS = ("547", "841", "1091")
MAX_LINES = 3
MAX_ENTRY_BYTES = 256
MAX_POOL_ENTRIES = 1024
MAX_FIT_EVALUATIONS = 163840
CPU_SECONDS_PER_FIT = 120.0


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


codec = load_module("readable_joint_codec", CODEC_FILE)
scorer = load_module("readable_joint_scorer", SCORER_FILE)


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def verify_alphabet_policy() -> dict:
    """Inspect the existing expression without importing its optimizer/deps."""
    raw = POLICY_FILE.read_bytes()
    tree = ast.parse(raw)
    matches = [node.value for node in tree.body if isinstance(node, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "ALPHABET" for t in node.targets)]
    expected = ast.parse("[chr(i) for i in range(32, 127)] + ['\\n']", mode="eval").body
    if len(matches) != 1 or ast.dump(matches[0]) != ast.dump(expected):
        raise ValueError("existing 96-character alphabet policy changed")
    return {"file": str(POLICY_FILE.relative_to(LIT)), "sha256": sha(raw),
            "entries": len(ALPHABET), "codepoints": [ord(x) for x in ALPHABET],
            "coverage": "95 printable ASCII characters U+0020..U+007E plus LF U+000A; not all ASCII controls"}


def validate_texts(texts: dict[str, str]) -> None:
    if not texts or any(not isinstance(t, str) or not t for t in texts.values()):
        raise ValueError("nonempty source strings required")
    for pid, text in texts.items():
        if set(text) - set(ALPHABET):
            raise ValueError(f"source {pid} is outside printable ASCII plus LF; no escape exists")


def candidate_pool(texts: dict[str, str], forbidden=()) -> list[str]:
    """Complete lines; 2/3-line windows must recur in two distinct programs.

    All strings contain their actual whitespace, identifiers and constants.
    The finite pool is not a grammar and contains no placeholders or expansion.
    """
    validate_texts(texts)
    banned = set(forbidden) | set(texts.values())
    stripped_banned = {text.strip() for text in banned}
    owners = {}
    for pid, text in sorted(texts.items()):
        lines = text.splitlines(keepends=True)
        for start in range(len(lines)):
            for count in range(1, MAX_LINES + 1):
                if start + count > len(lines):
                    break
                piece = "".join(lines[start:start + count])
                if (len(piece) < 2 or len(piece.encode()) > MAX_ENTRY_BYTES
                        or not piece.strip() or piece.strip() in stripped_banned):
                    continue
                owners.setdefault(piece, set()).add(pid)
    pool = sorted(piece for piece, pids in owners.items()
                  if len(piece.splitlines()) == 1 or len(pids) >= 2)
    if len(pool) > MAX_POOL_ENTRIES:
        raise ValueError("candidate pool exceeds frozen limit; no adaptive truncation")
    return pool


def occurrence_ends(text: str, piece: str) -> dict[int, int]:
    result = {}
    at = text.find(piece)
    while at >= 0:
        result[at] = at + len(piece)
        at = text.find(piece, at + 1)
    return result


def minimum_count(length: int, edges: list[list[int]], optional: dict[int, int]) -> int:
    """Unit-cost path count for selected edges plus exactly one trial entry."""
    costs = [0] * (length + 1)
    for at in range(length - 1, -1, -1):
        best = costs[at + 1]  # Every character is a paid dictionary entry.
        for end in edges[at]:
            best = min(best, costs[end])
        if at in optional:
            best = min(best, costs[optional[at]])
        costs[at] = 1 + best
    return costs[0]


def fit_dictionary(texts: dict[str, str], capacity: int, forbidden=()) -> tuple[list[str], dict]:
    """Deterministic greedy exact marginal count, with no pruning/restarts.

    CPU expiry is a retained failure, never a smaller machine-dependent result.
    A full exact re-score and canonical segmentation checks every accepted move.
    """
    if capacity not in (128, 256):
        raise ValueError("only frozen 128/256-entry caps are supported")
    pool = candidate_pool(texts, forbidden)
    started = time.process_time()
    keys = sorted(texts)
    occurrences = {piece: [occurrence_ends(texts[p], piece) for p in keys] for piece in pool}
    edges = [[[] for _ in texts[p]] for p in keys]
    chosen, remaining, trace = [], set(pool), []
    incumbent = sum(map(len, texts.values()))
    evaluations = 0
    while remaining and len(chosen) < capacity - len(ALPHABET):
        trials = []
        for piece in sorted(remaining):
            evaluations += 1
            if evaluations > MAX_FIT_EVALUATIONS or time.process_time() - started > CPU_SECONDS_PER_FIT:
                raise RuntimeError("frozen fit budget exceeded; arm failed, no partial dictionary accepted")
            count = sum(minimum_count(len(texts[p]), edges[i], occurrences[piece][i])
                        for i, p in enumerate(keys))
            # Minimize exact N; equal N prefers fewer added bytes, then literal UTF-8 order.
            trials.append((count, len(piece.encode()), piece))
        count, _, piece = min(trials)
        if count >= incumbent:
            break
        chosen.append(piece)
        remaining.remove(piece)
        for i in range(len(keys)):
            for at, end in occurrences[piece][i].items():
                edges[i][at].append(end)
        vocabulary = ALPHABET + sorted(chosen)
        actual = sum(len(scorer.shortest_encode(texts[p], vocabulary)) for p in keys)
        if actual != count:
            raise AssertionError("fit graph disagrees with existing exact scorer")
        trace.append({"step": len(chosen), "literal": piece, "before": incumbent,
                      "after": count, "gain": incumbent - count})
        incumbent = count
    vocabulary = ALPHABET + sorted(chosen)
    return vocabulary, {"pool_entries": len(pool), "pool_sha256": sha(json.dumps(pool).encode()),
                        "evaluations": evaluations, "accepted_additions": len(trace), "trace": trace,
                        "fit_total_selections": incumbent, "cpu_seconds": time.process_time() - started,
                        "termination": "capacity" if len(vocabulary) == capacity else "no_positive_gain"}


def independent_decode(dictionary: bytes, packet: bytes) -> bytes:
    """Separate integer bit reader: rejects malformed framing, IDs and padding."""
    if len(dictionary) < 8 or dictionary[:4] != b"LTD1":
        raise ValueError("dictionary header")
    count = int.from_bytes(dictionary[4:8], "big")
    if not 0 < count <= 256:
        raise ValueError("dictionary count")
    pos, literals = 8, []
    for _ in range(count):
        if pos + 4 > len(dictionary):
            raise ValueError("dictionary length")
        length = int.from_bytes(dictionary[pos:pos + 4], "big")
        pos += 4
        if not length or pos + length > len(dictionary):
            raise ValueError("dictionary entry")
        value = dictionary[pos:pos + length]
        value.decode("utf-8")
        literals.append(value)
        pos += length
    if pos != len(dictionary) or len(set(literals)) != count:
        raise ValueError("dictionary trailing data or duplicate")
    if len(packet) < 41 or packet[:4] != b"LTV1":
        raise ValueError("packet header")
    width, count = packet[4], int.from_bytes(packet[37:41], "big")
    if not 1 <= width <= 8 or len(literals) > 2 ** width:
        raise ValueError("packet width")
    if packet[5:37] != hashlib.sha256(dictionary).digest():
        raise ValueError("packet dictionary identity")
    bits = count * width
    if len(packet) != 41 + (bits + 7) // 8:
        raise ValueError("packet length")
    payload = int.from_bytes(packet[41:], "big")
    padding = (-bits) % 8
    if payload & ((1 << padding) - 1):
        raise ValueError("packet padding")
    result = []
    for index in range(count):
        shift = bits + padding - (index + 1) * width
        entry = (payload >> shift) & ((1 << width) - 1)
        if entry >= len(literals):
            raise ValueError("unused dictionary ID")
        result.append(literals[entry])
    return b"".join(result)


def measure(texts: dict[str, str], vocabulary: list[str], width: int) -> tuple[dict, dict]:
    validate_texts(texts)
    if vocabulary[:96] != ALPHABET or len(vocabulary) > 2 ** width:
        raise ValueError("alphabet/capacity contract")
    if set(vocabulary) & set(texts.values()):
        raise ValueError("whole-source entry")
    dictionary = scorer.dictionary_bytes(vocabulary)
    binary_literals = [x.encode() for x in vocabulary]
    rows, packets, uses = {}, {}, {i: [] for i in range(len(vocabulary))}
    for pid, text in sorted(texts.items()):
        sequence = scorer.shortest_encode(text, vocabulary)
        other, absent = codec.parse(text.encode(), binary_literals)
        if other != sequence or absent:
            raise AssertionError("exact scorers disagree")
        packet = codec.packet(sequence, width, dictionary)
        codec.verify_packet(packet, dictionary, binary_literals, text.encode())
        if independent_decode(dictionary, packet) != text.encode():
            raise AssertionError("independent decode mismatch")
        characters = sum(len(vocabulary[index]) == 1 for index in sequence)
        for index in set(sequence):
            uses[index].append(pid)
        rows[pid] = {"source_sha256": sha(text.encode()), "source_utf8_bytes": len(text.encode()),
                     "selections": len(sequence), "sequence": sequence,
                     "selection_bits": width * len(sequence), "single_character_selections": characters,
                     "single_character_bits": width * characters,
                     "single_character_bit_fraction": characters / len(sequence),
                     "packet_bytes": len(packet), "packet_sha256": sha(packet),
                     "framing_bytes": 41, "padding_bits": (-width * len(sequence)) % 8,
                     "largest_selected_literal_bytes": max(len(vocabulary[i].encode()) for i in sequence)}
        packets[pid] = packet
    counts = [row["selections"] for row in rows.values()]
    total = sum(counts)
    characters = sum(row["single_character_selections"] for row in rows.values())
    packet_bytes = sum(map(len, packets.values()))
    summary = {"programs": len(rows), "entries": len(vocabulary), "width": width,
               "source_utf8_bytes": sum(row["source_utf8_bytes"] for row in rows.values()),
               "dictionary_utf8_bytes": sum(map(len, binary_literals)),
               "dictionary_framing_bytes": 8 + 4 * len(vocabulary),
               "dictionary_bytes": len(dictionary), "dictionary_sha256": sha(dictionary),
               "packet_bytes": packet_bytes, "packet_framing_bytes": 41 * len(rows),
               "padding_bits": sum(row["padding_bits"] for row in rows.values()),
               "package_bytes": len(dictionary) + packet_bytes,
               "decoder_source_bytes": CODEC_FILE.stat().st_size,
               "package_plus_decoder_bytes": len(dictionary) + packet_bytes + CODEC_FILE.stat().st_size,
               "selections": total, "median": statistics.median(counts),
               "p95": sorted(counts)[math.ceil(.95 * len(counts)) - 1], "worst": max(counts),
               "selection_bits": total * width, "single_character_bits": characters * width,
               "single_character_bit_fraction": characters / total,
               "whole_solution_entries": 0,
               "used_entries": sum(bool(owners) for owners in uses.values()),
               "reused_noncharacter_entries": [i for i, owners in uses.items()
                                                if len(owners) >= 2 and len(vocabulary[i]) > 1],
               "entry_problem_support": {str(i): owners for i, owners in uses.items() if owners},
               "per_problem": rows}
    return summary, {"dictionary": dictionary, "packets": packets}


def source_identities(sources: dict) -> list[dict]:
    if set(sources) != set(LANGUAGES):
        raise ValueError("unexpected languages")
    result = []
    for language in LANGUAGES:
        if set(sources[language]) != set(PROBLEMS):
            raise ValueError("unexpected problem population")
        for pid in PROBLEMS:
            if set(sources[language][pid]) != set(VARIANTS):
                raise ValueError("unexpected source variants")
            validate_texts(sources[language][pid])
            for variant in VARIANTS:
                text = sources[language][pid][variant]
                result.append({"language": language, "problem_id": pid, "variant": variant,
                               "sha256": sha(text.encode()), "source_utf8_bytes": len(text.encode())})
    return result


def require_qualification(receipt: dict, identities: list[dict], contract: dict) -> None:
    if (receipt.get("schema") != "gamma.readable-joint-blocks.qualification.v1"
            or receipt.get("status") != "passed" or receipt.get("success") is not True):
        raise ValueError("successful fresh isolated qualification required before fitting")
    expected = {(row["language"], row["problem_id"], row["variant"]): row["sha256"] for row in identities}
    counts = contract["cases_by_problem"]
    batch = contract["batch_cases"]
    executions = sum(math.ceil(counts[pid] / batch) for _, pid, _ in expected)
    if (receipt.get("failures") != [] or type(receipt.get("candidate_executions")) is not int
            or receipt["candidate_executions"] != executions
            or receipt.get("protected_access") is not False
            or receipt.get("cases_sha256") != contract["cases_sha256"]
            or receipt.get("code_sha256") != contract["code_sha256"]):
        raise ValueError("qualification case/code identity, execution coverage or failures mismatch")
    rows = receipt.get("rows", [])
    seen = set()
    for row in rows:
        key = (row.get("language"), row.get("problem_id"), row.get("variant"))
        total, passed = row.get("checks_total"), row.get("checks_passed")
        independent = row.get("independent_oracle_checks_total")
        compatibility = row.get("predecessor_compatibility_checks_total")
        if (key in seen or key not in expected or row.get("sha256") != expected[key]
                or row.get("passed") is not True or type(total) is not int or total != counts.get(key[1])
                or total <= 0
                or type(passed) is not int or passed != total
                or type(independent) is not int or type(compatibility) is not int
                or min(independent, compatibility) < 0 or independent + compatibility != total):
            raise ValueError("incomplete, stale, duplicated or failed qualification row")
        seen.add(key)
    if seen != set(expected):
        raise ValueError("qualification does not cover all frozen source variants")


def validate_qualification_bundle(path: Path, identities: list[dict]) -> dict:
    """Recheck the actual contract and every saved observation, not pass flags.

    Rebuilding public/synthetic cases and replaying host comparisons never runs
    candidate source. These files are evidence artifacts, not signed attestations.
    """
    receipt = json.loads(path.read_text())
    if receipt.get("status") != "passed" or receipt.get("success") is not True:
        raise ValueError("successful fresh isolated qualification required before fitting")
    raw = (path.parent / "contract.json").read_bytes()
    contract = json.loads(raw)
    if receipt.get("qualification_contract_sha256") != sha(raw):
        raise ValueError("qualification contract identity mismatch")
    qualifier = load_module("readable_joint_qualifier", HERE / "qualify.py")
    cases = qualifier.build_cases()
    expected = {
        "schema": qualifier.SCHEMA, "seed": qualifier.SEED,
        "sources": qualifier.provenance(), "cases_sha256": sha(qualifier.json_bytes(cases)),
        "code_sha256": {name: sha((HERE / name).read_bytes())
                        for name in ("variants.py", "qualify.py", "QUALIFICATION.md")},
        "cases_by_problem": {pid: len(values) for pid, values in cases.items()},
        "case_origin": "synthetic_and_public_samples_only", "max_total_wall_seconds": 180,
        "batch_cases": 128, "sandbox": "existing_algsolve.judge.sandbox.run_unmodified",
        "sandbox_sha256": sha(Path(qualifier.sandbox.__file__).read_bytes()),
        "runtime_paths": {"python": "/usr/bin/python3", "javascript": "/usr/bin/node"},
        "protected_access": False,
    }
    if contract != expected:
        raise ValueError("qualification cases, sources, code, sandbox or schedule changed")
    require_qualification(receipt, identities, contract)
    rows = {(row["language"], row["problem_id"], row["variant"]): row for row in receipt["rows"]}
    for row in rows.values():
        problem_cases = cases[row["problem_id"]]
        if (row["independent_oracle_checks_total"] != sum(c["expectation_mode"] == "independent-oracle" for c in problem_cases)
                or row["predecessor_compatibility_checks_total"] != sum(c["expectation_mode"] == "predecessor-effect-compatibility" for c in problem_cases)):
            raise ValueError("qualification oracle/compatibility evidence classes changed")
    for language in LANGUAGES:
        for pid in PROBLEMS:
            original = []
            for variant in VARIANTS:
                passed, observations = 0, []
                for offset in range(0, len(cases[pid]), contract["batch_cases"]):
                    batch = cases[pid][offset:offset + contract["batch_cases"]]
                    stem = path.parent / f"{language}-{pid}-{variant}-{offset}"
                    records = qualifier.parse_records(stem.with_suffix(".stdout").read_bytes(), len(batch))
                    # Both outputs must have been retained, even if stderr is empty.
                    stem.with_suffix(".stderr").read_bytes()
                    for index, (case, record) in enumerate(zip(batch, records)):
                        baseline = None if variant == "original" else original[offset + index]
                        passed += int(qualifier.judge_record(pid, case, record, baseline))
                    observations.extend(records)
                if passed != rows[language, pid, variant]["checks_total"]:
                    raise ValueError("qualification observations fail independent replay")
                if variant == "original":
                    original = observations
    return receipt


def pinned_files() -> list[Path]:
    return [HERE / "compare.py", HERE / "test_compare.py", HERE / "FREEZE.md",
            HERE / "variants.py", HERE / "qualify.py", HERE / "QUALIFICATION.md",
            CODEC_FILE, SCORER_FILE, POLICY_FILE,
            LIT.parent / "algsolve" / "judge" / "sandbox.py",
            *[LIT / "readable-v1" / "fixtures" / f"{pid}.json" for pid in PROBLEMS]]


def pin_name(path: Path) -> str:
    # All pins are code/public fixture paths under algorithm_solver, not corpus paths.
    return str(path.relative_to(LIT.parent))


def freeze(output: Path) -> dict:
    variants = load_module("readable_joint_variants", HERE / "variants.py")
    sources = variants.build_sources()
    contract = {"schema": "gamma.readable-joint-blocks.comparison-freeze.v1",
                "source_identities": source_identities(sources), "provenance": variants.provenance(),
                "alphabet": verify_alphabet_policy(), "capacities": [128, 256],
                "source_choices": list(VARIANTS), "dictionary_fit_sources": list(VARIANTS),
                "candidate_policy": {"max_lines": MAX_LINES, "max_entry_bytes": MAX_ENTRY_BYTES,
                    "multiline_min_distinct_programs": 2, "max_pool_entries": MAX_POOL_ENTRIES},
                "budget": {"max_fit_evaluations": MAX_FIT_EVALUATIONS,
                    "cpu_seconds_per_fit": CPU_SECONDS_PER_FIT, "restarts": 0},
                "code_sha256": {pin_name(path): sha(path.read_bytes()) for path in pinned_files()},
                "python": platform.python_version(), "candidate_execution": False,
                "protected_data_access": False, "qualification_required_before_fit": True,
                "scope": "3 exposed development problems per language; no M1/M2/M3 claim"}
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "contract.json", contract)
    return contract


def validate_freeze(contract: dict, sources: dict) -> None:
    if contract.get("schema") != "gamma.readable-joint-blocks.comparison-freeze.v1":
        raise ValueError("comparison freeze schema")
    if contract["source_identities"] != source_identities(sources):
        raise ValueError("source changed after freeze")
    expected_files = {pin_name(path) for path in pinned_files()}
    if set(contract["code_sha256"]) != expected_files:
        raise ValueError("incomplete frozen code identities")
    for relative, digest in contract["code_sha256"].items():
        if sha((LIT.parent / relative).read_bytes()) != digest:
            raise ValueError(f"code changed after freeze: {relative}")
    if contract["alphabet"] != verify_alphabet_policy():
        raise ValueError("alphabet changed after freeze")


def run(frozen: Path, qualification: Path, output: Path) -> dict:
    if not __debug__:
        raise RuntimeError("assertions must remain enabled in the retained codec")
    contract = json.loads((frozen / "contract.json").read_text())
    sources = load_module("readable_joint_variants", HERE / "variants.py").build_sources()
    validate_freeze(contract, sources)
    receipt = validate_qualification_bundle(qualification, contract["source_identities"])
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "contract.json", contract)
    result = {"schema": "gamma.readable-joint-blocks.comparison.v1", "status": "running",
              "freeze_sha256": sha((frozen / "contract.json").read_bytes()),
              "qualification_sha256": sha(qualification.read_bytes()),
              "qualification_contract_sha256": receipt.get("qualification_contract_sha256"),
              "candidate_execution": False, "protected_data_access": False,
              "decoder_sha256": sha(CODEC_FILE.read_bytes()), "profiles": [], "fits": [],
              "scope": contract["scope"], "m1_qualified": False}
    try:
        for language in LANGUAGES:
            forbidden = [t for versions in sources[language].values() for t in versions.values()]
            for capacity in (128, 256):
                width = capacity.bit_length() - 1
                # Original is fitted/sealed first, then never edited for shared-source scoring.
                for fit_source in VARIANTS:
                    texts = {pid: versions[fit_source] for pid, versions in sources[language].items()}
                    vocabulary, trace = fit_dictionary(texts, capacity, forbidden)
                    fit_id = f"{language}-{capacity}-{fit_source}"
                    fit_dir = output / fit_id
                    fit_dir.mkdir()
                    write_json(fit_dir / "dictionary.json", vocabulary)
                    write_json(fit_dir / "fit.json", trace)
                    result["fits"].append({"id": fit_id, **trace})
                    for source_variant in VARIANTS:
                        texts = {pid: versions[source_variant] for pid, versions in sources[language].items()}
                        profile, binary = measure(texts, vocabulary, width)
                        (fit_dir / "dictionary.ltd").write_bytes(binary["dictionary"])
                        for pid, packet in binary["packets"].items():
                            (fit_dir / f"{source_variant}-{pid}.ltv").write_bytes(packet)
                        result["profiles"].append({"id": f"{fit_id}-on-{source_variant}",
                            "language": language, "capacity": capacity, "source_variant": source_variant,
                            "dictionary_fit_source": fit_source, **profile})
        result["status"] = "completed"
    except Exception as exc:
        result["status"] = "failed"
        result["failure"] = {"type": type(exc).__name__, "reason": str(exc)}
        write_json(output / "results.json", result)
        raise
    write_json(output / "results.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    freezing = subparsers.add_parser("freeze")
    freezing.add_argument("--output", type=Path, required=True)
    running = subparsers.add_parser("run")
    running.add_argument("--freeze", type=Path, required=True)
    running.add_argument("--qualification", type=Path, required=True)
    running.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = freeze(args.output) if args.command == "freeze" else run(args.freeze, args.qualification, args.output)
    print(json.dumps({"status": result.get("status", "frozen"), "output": str(args.output)}))


if __name__ == "__main__":
    main()
