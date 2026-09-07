#!/usr/bin/env python3
"""Print records for the closed literal-first diagnostic; never run a codec."""
import hashlib
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import research_contracts
import dualstream_literal_first_gate_v1 as gate

CID = "dualstream_literal_first250k_q0_v1"
DEST = "operations/provenance/dualstream_literal_first_terminal_20260907"
RESULT = "results/" + CID + "/"


def load(path):
    return json.loads((ROOT / path).read_text())


def ref(path):
    return dict(path=path, sha256="sha256:" + hashlib.sha256((ROOT / path).read_bytes()).hexdigest())


def verify(row):
    assert ref(row["path"])["sha256"].removeprefix("sha256:") == row["sha256"].removeprefix("sha256:"), row["path"]
    if "bytes" in row:
        assert (ROOT / row["path"]).stat().st_size == row["bytes"]


def main():
    contract_path = "operations/adaptive/experiments/" + CID + ".json"
    contract = load(contract_path)
    research_contracts.validate_artifact(ROOT / contract_path, verify_files=True)
    candidates = [p for p in (ROOT / "operations/adaptive/completed").glob("*.json") if json.loads(p.read_text()).get("candidate_id") == CID]
    assert len(candidates) == 1
    job_path = str(candidates[0].relative_to(ROOT))
    job = load(job_path)
    jid = job["job_id"]
    guard_path = "run_logs/adaptive/" + jid + ".resources/guard.json"
    guard, stage = load(guard_path), load(RESULT + "stage-decision.json")
    assert job["state"] == "completed" and job["returncode"] == 0 and job["execution_resources"]["cleanup_complete"]
    assert guard["status"] == "complete" and guard["returncode"] == 0 and not any(guard["guards"].values())
    assert not guard["latest_sample"]["processes"]
    assert all(stage[k] for k in ("correctness_pass", "accounting_pass", "p_k_archive_identity_pass", "raw_encoder_repeat_proved", "frozen_inputs_reverified"))
    assert stage["native_phases"] == len(stage["commands"]) == 9
    assert all(p["returncode"] == 0 and not p["timeout"] and p["error"] is None for p in stage["commands"])
    for row in contract["inputs"] + load(RESULT + "artifacts.json")["files"]:
        verify(row)
    revision = dict(candidateId=CID, candidateTreeSha256=job["candidate_tree_sha256"], receipt=job["candidate_revision"])
    outputs = {}
    index = dict(schema="gamma.enwiki9.terminal-result-index.v1", job=ref(job_path), guard=ref(guard_path), arms=[],
                 evidence=[ref(RESULT + "stage-decision.json"), ref(RESULT + "costs-table.json")])
    raw_path = "operations/evidence/fixtures/dualstream_opening250k_v1.raw"
    raw = (ROOT / raw_path).read_bytes()
    for row in stage["arms"]:
        arm = row["arm"]["id"]
        for artifact in row["artifacts"].values():
            verify(artifact)
        archive, inverse, repeat = [(ROOT / row["artifacts"][key]["path"]).read_bytes() for key in ("archive", "restored", "repeat")]
        assert inverse == raw and archive == repeat and len(archive) == row["archive_bytes"] == sum(row["accounting"].values())
        encoded, decoded, repeated = [load(RESULT + arm + "-" + phase + ".stdout") for phase in ("encode", "decode", "repeat")]
        assert encoded["result"] == repeated["result"]
        if arm != "P":
            assert gate.common_report(encoded["result"]) == gate.common_report(decoded["result"])
        result = dict(schema="gamma.enwiki9.driver-result.v2", program_id=CID, program_name="Literal-first grammar " + arm,
            arm=arm, candidate_revision=revision, objective=contract["objective"], timestamp=job["finished_at"],
            run_source=job_path, run_purpose="diagnostic", run_scope_label="opening250KB-literal-first-" + arm,
            run_tags=["literal-first", "raw-discovery", "diagnostic", arm], data_path=raw_path, data_size=len(raw),
            data_sha256=hashlib.sha256(raw).hexdigest(), data_md5=hashlib.md5(raw).hexdigest(),
            compressed_size=len(archive), compressed_sha256=hashlib.sha256(archive).hexdigest(), compressed_md5=hashlib.md5(archive).hexdigest(),
            bits_per_byte=8 * len(archive) / len(raw), program_size=None, hutter_score=None,
            hutter_score_kind="diagnostic-literal-first-grammar", complete_package_bytes=None, full_corpus_score_bytes=None,
            prize_claimable=False, score_accounting_complete=False, resource_evidence_complete=False,
            qualification_status="not-certified", execution_mode="discovery", timing_authority="diagnostic", roundtrip_ok=True,
            determinism=dict(scope="single-host", single_host_byte_equal=True), raw_encoder_repeat_proved=True,
            repeat_scope="raw-discovery-and-encoding", compress_time_s=encoded["elapsed_seconds"], decompress_time_s=decoded["elapsed_seconds"],
            encoding_cpu_seconds=encoded["cpu_seconds"], decoding_cpu_seconds=decoded["cpu_seconds"], repeat_time_s=repeated["elapsed_seconds"],
            run_time_s=sum(p["elapsed_seconds"] for p in stage["commands"] if p["phase"].startswith(arm + "-")),
            run_time_scope="Raw encoding, independent decoding and renewed raw encoding with discovery.",
            memory_kib=dict(peak=max(p["peak_process_rss_kib"] for p in (encoded, decoded, repeated))),
            host=dict(machine=platform.machine(), node=platform.node(), python=platform.python_version(), system=platform.system()),
            accounting=row["accounting"], artifacts=row["artifacts"],
            missing_diagnostics=job["execution_resources"]["missing_diagnostics"], closed_guard=ref(guard_path), closed_job=ref(job_path),
            source_arm_result=ref(RESULT + arm + ".result.json"),
            run_context="Whole-frame cost admission over exact literal spans and shared template arguments; P/K identical. Package qualification unknown.",
            deterministic_repeat=dict(single_host_byte_equal=True, selection_repeated=arm != "P",
                first_run_sha256=hashlib.sha256(archive).hexdigest(), second_run_sha256=hashlib.sha256(repeat).hexdigest(),
                first_run_md5=hashlib.md5(archive).hexdigest(), second_run_md5=hashlib.md5(repeat).hexdigest(), first_divergence_byte=None))
        out = DEST + "/normalized/" + arm + ".json"
        outputs[out] = result
        data = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
        index["arms"].append(dict(arm=arm, result=dict(path=out, sha256="sha256:" + hashlib.sha256(data).hexdigest()), artifacts=row["artifacts"]))
    costs = stage["costs"]
    measurements = dict(correctness_pass=True, frozen_inputs_reverified=True, continuous_guard_pass=True, artifact_closure_pass=True,
        accounting_pass=True, p_k_archive_identity_pass=True, raw_encoder_repeat_proved=True,
        promotion_authorized=False, scientific_rejection_applicable=False, native_phases=9, raw_bytes=len(raw),
        p_minus_d_bytes=costs["p_minus_d_bytes"], p_minus_k_bytes=costs["p_minus_k_bytes"],
        strict_d_improvement=costs["strict_d_improvement"])
    artifacts = [dict(id="artifact-" + str(i), **ref(path)) for i, path in enumerate(contract["outputs"]) if path != RESULT + "decision.json"]
    def predicates(key):
        return [dict(p, observed=measurements[p["measurement"]], passed=measurements[p["measurement"]] == p["threshold"]) for p in contract[key]]
    outputs[RESULT + "decision.json"] = dict(schema="gamma.enwiki9.adaptive-experiment-result.v1", objective=contract["objective"],
        experiment=ref(contract_path), candidateId=CID, candidateRevision=revision, evidenceClass="diagnostic", objectiveCreditBytes=0,
        measurements=measurements, promotionPredicates=predicates("promotionPredicates"), killPredicates=predicates("killPredicates"),
        promotionPass=False, killPass=False, decision="retry", artifacts=artifacts, generatedUtc=job["finished_at"])
    outputs[DEST + "/index.json"] = index
    outputs[DEST + ".json"] = dict(schema="gamma.enwiki9.literal-first-terminal.v1", candidate_id=CID,
        job=ref(job_path), guard=ref(guard_path), experiment=ref(contract_path), stage=ref(RESULT + "stage-decision.json"),
        measurements=measurements, costs=costs,
        gate_resources=dict(elapsed_seconds=guard["elapsed_s"], peaks=guard["peaks"], samples=guard["sample_count"], guards=guard["guards"]),
        template_counts={r["arm"]["id"]:{k:r[k] for k in ("selected_rules", "calls", "repeated_argument_references")} for r in stage["arms"]},
        route="Eligible for separately frozen fresh confirmation" if costs["strict_d_improvement"] else "Park this realization; fallback equality grants no confirmation",
        limits=["No full-corpus score or projection.", "Joint compressed byte costs do not attribute predictive savings to individual representation sections.",
                "Runtime/source/license/options qualification remains unresolved.", "This bounded span/proposal search does not exhaust possible templates."],
        full_corpus_score_bytes=None, complete_package_bytes=None, objective_credit_bytes=0)
    print(json.dumps({path:json.dumps(value, indent=2, sort_keys=True) + "\n" for path,value in outputs.items()}))


if __name__ == "__main__":
    main()
