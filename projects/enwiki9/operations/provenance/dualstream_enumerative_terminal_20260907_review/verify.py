#!/usr/bin/env python3
"""Audit closed receipts and transmitted integer widths; never run a codec."""
from pathlib import Path
import hashlib
import json
import math
import os
import resource
import struct
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CID = "dualstream_enumerative250k_q0_v3"
JID = "20260907T163610Z_dfcedb020f"
RESULTS = ROOT / "results" / CID
NAMES = ("literal_definitions", "grammar_programs", "structure", "content", "arguments")
FRAME = struct.Struct("<IB5I32s")
LEGACY = struct.Struct("<8sIIQ")
ENUM = struct.Struct("<8sBIIIQ")
CHECKS = []
FILES = {}


def check(value, label):
    if not value:
        raise AssertionError(label)
    CHECKS.append(label)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    data = path.read_bytes()
    name = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    FILES[name] = dict(path=name, bytes=len(data), sha256=digest(data))
    return data


def document(path):
    return json.loads(read(path))


def reference(ref):
    data = read(ref.get("path", ref.get("blobPath")))
    check(digest(data) == ref["sha256"].removeprefix("sha256:"), "hash " + ref.get("path", ref.get("blobPath")))
    if "bytes" in ref:
        check(len(data) == ref["bytes"], "length " + ref.get("path", ref.get("blobPath")))
    return data


class Reader:
    def __init__(self, data):
        self.data, self.offset = data, 0

    def take(self, size):
        check(0 <= size <= len(self.data) - self.offset, "bounded archive slice")
        value = self.data[self.offset:self.offset + size]
        self.offset += size
        return value

    def number(self):
        result = 0
        for shift in range(0, 63, 7):
            value = self.take(1)[0]
            result |= (value & 127) << shift
            if value < 128:
                check(shift == 0 or value != 0, "canonical integer")
                return result
        raise AssertionError("unbounded integer")

    def end(self):
        check(self.offset == len(self.data), "exact section/archive consumption")


def enumerate_cost(encoded):
    """Inspect count tables and ranks without unranking or decoding symbols."""
    reader = Reader(encoded)
    size = reader.number()
    check(size <= 1048576, "bounded raw section")
    result = dict(raw_serialized_bytes=size, rank_bytes=0, count_table_bytes=0,
                  stream_header_bytes=reader.offset, chunks=0, encoded_bytes=len(encoded))
    remaining = size
    while remaining:
        expected = min(4096, remaining)
        start = reader.offset
        entries = reader.number()
        check(1 <= entries <= min(256, expected), "bounded count alphabet")
        previous, counts = -1, []
        for _ in range(entries):
            symbol, count = reader.take(1)[0], reader.number()
            check(symbol > previous and count > 0, "ordered positive count table")
            previous = symbol
            counts.append(count)
        check(sum(counts) == expected, "exact count total")
        # Independent expression from the codec's product of binomials.
        possibilities = math.factorial(expected) // math.prod(math.factorial(c) for c in counts)
        width, capacity = 0, 1
        while capacity < possibilities:
            capacity *= 256
            width += 1
        result["count_table_bytes"] += reader.offset - start
        rank = int.from_bytes(reader.take(width), "big")
        check(rank < possibilities, "stored rank inside exact type class")
        result["rank_bytes"] += width
        result["chunks"] += 1
        remaining -= expected
    reader.end()
    check(result["rank_bytes"] + result["count_table_bytes"] + result["stream_header_bytes"] == len(encoded),
          "independent transmitted section total")
    return result


def inspect_archive(data, report, enumerative, raw):
    reader = Reader(data)
    if enumerative:
        magic, storage, chunk, frame_size, frames, total = ENUM.unpack(reader.take(ENUM.size))
        check(magic == b"D2ENUM01" and chunk == 4096, "enumerative header")
        check(storage == int(report["storage"] == "new"), "explicit argument frontend")
    else:
        magic, frame_size, frames, total = LEGACY.unpack(reader.take(LEGACY.size))
        check(magic in (b"D2GRAM01", b"D2GRAM02"), "explicit retained frontend")
    check(frame_size == 65536 and frames == 4 and total == len(raw) == 250000, "fixed raw frame population")
    summaries, offset = [], 0
    for index in range(frames):
        size, mode, *tail = FRAME.unpack(reader.take(FRAME.size))
        check(size == min(frame_size, total - offset), "frame raw length")
        check(digest(raw[offset:offset + size]) == tail[5].hex(), "frame source hash")
        recorded = report["frames"][index]
        check(recorded["raw_bytes"] == size and recorded["raw_sha256"] == tail[5].hex(), "frame receipt identity")
        chunks = [reader.take(size) for size in tail[:5]]
        if enumerative:
            check(mode == recorded["mode"], "enumerative mode receipt")
            sections = {}
            for name, encoded in zip(NAMES, chunks):
                measured = enumerate_cost(encoded)
                check(all(recorded["sections"][name][k] == v for k, v in measured.items()), "section cost receipt " + name)
                sections[name] = measured
            summaries.append(sections)
        else:
            costs = dict(literal_definition_bytes=len(chunks[0]), structure_bytes=len(chunks[1]) + len(chunks[2]),
                         content_bytes=len(chunks[3]), argument_reference_bytes=len(chunks[4]),
                         exception_bytes=0, framing_bytes=FRAME.size)
            check(all(recorded[k] == v for k, v in costs.items()), "independent Deflate framed costs")
            check(recorded["complete_archive_bytes"] == FRAME.size + sum(map(len, chunks)), "Deflate frame total")
        offset += size
    reader.end()
    if enumerative:
        costs = {name + "_rank_bytes": sum(s[name]["rank_bytes"] for s in summaries) for name in NAMES}
        costs.update(count_table_bytes=sum(s[n]["count_table_bytes"] for s in summaries for n in NAMES),
                     stream_header_bytes=sum(s[n]["stream_header_bytes"] for s in summaries for n in NAMES),
                     framing_bytes=ENUM.size + frames * FRAME.size, exception_bytes=0)
        check(costs == report["costs"] and sum(costs.values()) == len(data), "independent complete rank-size certificate")
    return summaries


def main():
    os.sched_setaffinity(0, {3})
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
    start, cpu = time.monotonic(), time.process_time()
    job = document("operations/adaptive/completed/909_" + JID + ".json")
    check(job["state"] == "completed" and job["returncode"] == 0, "canonical terminal job")
    check(job["execution_resources"]["cleanup_complete"], "resource cleanup completed")
    contract = json.loads(reference(job["experiment"]))
    check(contract["experimentId"] == CID and contract["objective"]["targetScoreBytes"] == 99000000, "frozen objective identity")
    for ref in contract["inputs"]:
        reference(ref)
    revision = json.loads(reference(job["candidate_revision"]))
    check(revision["candidateTreeSha256"] == job["candidate_tree_sha256"], "sealed candidate tree")
    for ref in revision["files"]:
        reference(dict(path=ref["blobPath"], bytes=ref["bytes"], sha256=ref["sha256"]))
    plan_ref = next(r for r in contract["inputs"] if r["id"] == "grammar-gate-plan")
    plan = document(plan_ref["path"])
    for ref in plan["runtime_files"]:
        reference(ref)
    for key, value in plan["resources"].items():
        check(job["resource_budget"][key] == value, "job resource " + key)
    guard = document(job["execution_resources"]["guard_path"])
    check(guard["status"] == "complete" and guard["returncode"] == 0 and not any(guard["guards"].values()), "closed passing guard")
    check(not guard["latest_sample"]["processes"] and guard["sample_count"] > 1, "closed sampled process tree")
    check(guard["peaks"]["cgroup_memory_peak_bytes"] <= plan["resources"]["memory_bytes"], "aggregate memory bound")
    check(guard["peaks"]["max_sampled_scratch_allocated_bytes"] <= plan["resources"]["scratch_bytes"], "allocated scratch bound")
    check(guard["elapsed_s"] <= plan["resources"]["wall_seconds"], "measured aggregate wall bound")
    check(guard["peak_sample"]["allowed_cpu_union"] == [2], "assigned discovery CPU")
    stage = document(RESULTS / "stage-decision.json")
    check(stage["status"] == "passed" and stage["correctness_pass"] and stage["frozen_inputs_reverified"], "closed valid scientific stage")
    index = document(RESULTS / "artifacts.json")
    check(index["complete"] and len(index["files"]) == 66, "complete runner artifact index")
    for ref in index["files"]:
        reference(ref)
    raw = reference(plan["population"])
    rows, reports, parsed = {}, {}, {}
    phases = []
    for arm in plan["arms"]:
        name = arm["id"]
        row = document(RESULTS / (name + ".result.json"))
        check(row["arm"] == arm and row in stage["arms"], "arm identity " + name)
        rows[name] = row
        for phase in ("encode", "decode", "repeat"):
            execution = document(RESULTS / (name + "-" + phase + ".execution.json"))
            check(execution["returncode"] == 0 and not execution["timeout"] and execution["error"] is None, "successful phase " + execution["phase"])
            check(execution in stage["commands"], "phase command identity")
            check(execution["elapsed_seconds"] <= plan["phase_wall_seconds"], "phase wall bound")
            check(execution["user_cpu_seconds"] + execution["system_cpu_seconds"] <= plan["phase_cpu_seconds"], "phase CPU bound")
            printed = document(RESULTS / (name + "-" + phase + ".stdout"))
            check(printed["complete_package_bytes"] is None and printed["full_corpus_score_bytes"] is None, "no unsupported package/score")
            phases.append(dict(phase=execution["phase"], cpu_seconds=execution["user_cpu_seconds"] + execution["system_cpu_seconds"],
                               elapsed_seconds=execution["elapsed_seconds"], peak_rss_kib=printed["peak_process_rss_kib"]))
            reports[name + "-" + phase] = printed["result"]
        encoded = reference(row["artifacts"]["archive"])
        repeat = reference(row["artifacts"]["repeat"])
        restored = reference(row["artifacts"]["restored"])
        check(encoded == repeat and restored == raw, "retained exact inverse and repeat " + name)
        check(row["raw_encoder_repeat_proved"] is False and row["repeat_scope"] == "fixed-program-reserialization", "repeat scope " + name)
        check(reports[name + "-encode"] == reports[name + "-repeat"], "repeat report identity " + name)
        report = reports[name + "-encode"]
        check(report["raw_sha256"] == digest(raw) and report["raw_bytes"] == len(raw), "encoded raw identity " + name)
        check(row["archive_bytes"] == len(encoded) == sum(row["accounting"].values()), "row additive accounting " + name)
        is_enum = arm["backend"] == "enumerative"
        parsed[name] = inspect_archive(encoded, report, is_enum, raw)
        if is_enum:
            check(report["section_hashes"] == reports[name + "-decode"]["section_hashes"], "retained encoder/decoder section identity " + name)
        else:
            selected = plan["selected_archives"][arm["selection"]]
            check(encoded == reference(selected), "unchanged selected baseline " + name)
    expected_phases = [a["id"] + "-" + p for a in plan["arms"] for p in ("encode", "decode", "repeat")]
    check([p["phase"] for p in phases] == expected_phases and stage["native_phases"] == 15, "all fifteen phases")
    events = [(r["phase"], r["event"]) for r in guard["phase_markers"] if r["event"] in ("start", "end")]
    check(events == [(p, e) for p in expected_phases for e in ("start", "end")], "all phase markers paired")
    graphs = {n: [f["model_sha256"] for f in rows[n]["frames"]] for n in rows}
    check(graphs["B"] == graphs["E"] == graphs["T"], "retained fixed graph identities")
    for f, g in zip(rows["E"]["frames"], rows["T"]["frames"]):
        for name in ("grammar_programs", "structure", "content"):
            check(f["sections"][name] == g["sections"][name], "unchanged treatment section " + name)
    bindings = {n: sum(f["repeated_argument_references"] for f in rows[n]["frames"]) for n in rows}
    check(not any(bindings.values()), "zero shared argument binding activation")
    table = document(RESULTS / "costs-table.json")
    sizes = {n: rows[n]["archive_bytes"] for n in rows}
    check(table["archive_bytes"] == sizes, "terminal size table")
    check(table["enum_vs_fixed_deflate_saved_bytes"] == sizes["B"] - sizes["E"], "backend delta")
    check(table["token_argument_saved_bytes"] == sizes["E"] - sizes["T"], "argument delta")
    check(table["enum_vs_plain_deflate_saved_bytes"] == sizes["P"] - sizes["E"], "plain baseline delta")
    package = [dict(ref) for ref in table["package_source"]]
    for ref in package:
        reference(ref)
    deltas = {k: rows["T"]["accounting"][k] - rows["E"]["accounting"][k] for k in rows["E"]["accounting"]}
    sections = {n: {s: sum(f[s]["encoded_bytes"] for f in parsed[n]) for s in NAMES} for n in ("E", "T", "R")}
    audit = dict(schema="gamma.enwiki9.enumerative-terminal-independent-audit.v1", candidate_id=CID, job_id=JID,
                 pass_=True, checks=len(CHECKS), input_count=len(contract["inputs"]), indexed_artifacts=len(index["files"]),
                 archive_bytes=sizes, section_encoded_bytes=sections, treatment_minus_E_bytes=deltas,
                 treatment_minus_E_section_bytes={s: sections["T"][s] - sections["E"][s] for s in NAMES},
                 source_component_bytes=sum(r["bytes"] for r in package), phases=phases,
                 repeated_argument_references=bindings, exact_raw_bytes=250000,
                 retained_section_identity_scope="Compare retained independently produced encoder/decoder section hashes and fixed graph receipts; no decoder rerun.",
                 independent_math_scope="Parse transmitted counts, recompute factorial multinomial counts, minimum base-256 widths and actual totals without unranking.",
                 encoded_chunk_count=sum(f[s]["chunks"] for n in ("E", "T", "R") for f in parsed[n] for s in NAMES),
                 full_corpus_score_bytes=None, complete_package_bytes=None, objective_credit_bytes=0,
                 qualification=False, guard=dict(elapsed_seconds=guard["elapsed_s"], samples=guard["sample_count"],
                 cgroup_peak_bytes=guard["peaks"]["cgroup_memory_peak_bytes"], guard_flags=guard["guards"], cleanup_complete=True),
                 review_resources=dict(cpu_affinity=[3], cpu_seconds=time.process_time()-cpu, elapsed_seconds=time.monotonic()-start,
                 peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, cpu_limit_seconds=60, address_limit_bytes=512*1024**2))
    with (OUT / "audit.json").open("x") as stream:
        stream.write(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    with (OUT / "verified-inputs.json").open("x") as stream:
        stream.write(json.dumps(dict(files=list(FILES.values())), indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
