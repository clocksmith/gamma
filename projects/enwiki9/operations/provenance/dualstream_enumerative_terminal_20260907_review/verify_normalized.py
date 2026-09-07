#!/usr/bin/env python3
"""Read-only audit of normalized rows and generic artifact closure."""
import hashlib
import importlib.util
import json
from pathlib import Path
import os
import resource

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("enumerative_closed_review", HERE / "verify_v2.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
os.sched_setaffinity(0, {3})
resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
root = audit.ROOT
read, document, reference, check = audit.read, audit.document, audit.reference, audit.check
base = root / "operations/provenance/dualstream_enumerative_terminal_20260907"
index = document(base / "index.json")
for ref in index["evidence"] + [index["job"], index["guard"]]:
    reference(ref)
raw = read("operations/evidence/fixtures/dualstream_opening250k_v1.raw")
rows = {}
for item in index["arms"]:
    name = item["arm"]
    row = json.loads(reference(item["result"]))
    source = json.loads(reference(row["source_arm_result"]))
    archive = reference(item["artifacts"]["archive"])
    repeat = reference(item["artifacts"]["repeat"])
    restored = reference(item["artifacts"]["restored"])
    check(row["artifacts"] == source["artifacts"] == item["artifacts"], "normalized artifact identities " + name)
    check(archive == repeat and restored == raw, "normalized exact retained bytes " + name)
    check(row["compressed_size"] == len(archive) and row["data_size"] == len(raw), "normalized sizes " + name)
    check(row["compressed_sha256"] == audit.digest(archive) and row["data_sha256"] == audit.digest(raw), "normalized SHA256 " + name)
    check(row["compressed_md5"] == hashlib.md5(archive).hexdigest() and row["data_md5"] == hashlib.md5(raw).hexdigest(), "normalized MD5 " + name)
    check(row["bits_per_byte"] == len(archive) * 8 / len(raw), "normalized exact byte ratio " + name)
    check(row["accounting"] == source["accounting"] and sum(row["accounting"].values()) == len(archive), "normalized additive costs " + name)
    for key in ("hutter_score", "full_corpus_score_bytes", "complete_package_bytes", "program_size", "compress_time_s"):
        check(row[key] is None, "normalized unknown " + key)
    for key in ("prize_claimable", "score_accounting_complete", "resource_evidence_complete", "raw_encoder_repeat_proved"):
        check(row[key] is False, "normalized no qualification " + key)
    check(row["qualification_status"] == "not-certified" and row["roundtrip_ok"], "normalized correctness scope " + name)
    check(row["determinism"]["single_host_byte_equal"] is None and row["reserialization_repeat"]["single_host_byte_equal"] is True,
          "normalized distinction between discovery and fixed repeat " + name)
    check(row["repeat_scope"] == "fixed-program-reserialization" and not row["reserialization_repeat"]["selection_repeated"], "normalized repeat boundary " + name)
    totals, peaks = [], []
    for phase in ("encode", "decode", "repeat"):
        execution = document(audit.RESULTS / (name + "-" + phase + ".execution.json"))
        printed = document(audit.RESULTS / (name + "-" + phase + ".stdout"))
        totals.append(execution["elapsed_seconds"])
        peaks.append(printed["peak_process_rss_kib"])
        if phase == "decode":
            check(row["decompress_time_s"] == printed["elapsed_seconds"], "normalized decode timing " + name)
    check(row["run_time_s"] == sum(totals) and row["memory_kib"]["peak"] == max(peaks), "normalized measured duration and peak " + name)
    rows[name] = row["compressed_size"]
decision = document(audit.RESULTS / "decision.json")
check(len(decision["artifacts"]) == 68, "generic artifact closure count")
for ref in decision["artifacts"]:
    reference(ref)
check(not decision["promotionPass"] and decision["objectiveCreditBytes"] == 0, "generic no promotion or score credit")
terminal = document("operations/provenance/dualstream_enumerative_terminal_20260907.json")
for key in ("job", "guard", "stage", "experiment"):
    reference(terminal[key])
check(terminal["costs"]["archive_bytes"] == rows, "terminal sizes")
check(terminal["repeated_argument_references"] == dict(P=0, B=12, E=12, T=12, R=0), "terminal corrects prior zero-binding assumption")
check(terminal["enum_rank_payload_bytes"] == 128666, "terminal exact rank-byte subtotal")
with (HERE / "normalized-audit.json").open("x") as out:
    out.write(json.dumps(dict(schema="gamma.enwiki9.enumerative-normalized-review.v1", passed=True,
                             checks=len(audit.CHECKS), normalized_rows=len(rows), generic_artifacts=68,
                             source_and_evidence=list(audit.FILES.values()),
                             scientific_scope="No codec rerun; normalized retained evidence and declared unknowns checked."), indent=2, sort_keys=True) + "\n")
print(json.dumps(dict(passed=True, checks=len(audit.CHECKS), normalized_rows=len(rows), generic_artifacts=68)))
