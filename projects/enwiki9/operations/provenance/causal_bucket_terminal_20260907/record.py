#!/usr/bin/env python3
"""Print records for the closed causal-bucket diagnostic; never run a codec."""
import hashlib
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import research_contracts
import causal_bucket_gate_v2 as gate

CID = "causal_bucket250k_q0_v1"
DEST = "operations/provenance/causal_bucket_terminal_20260907"
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
    candidates = list((ROOT / "operations/adaptive/completed").glob("*20260907T193106Z_9f544523f2.json"))
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
    assert job["candidate_id"] == CID and stage["candidate_id"] == CID
    assert job["experiment"] == stage["experiment"] == ref(contract_path)
    verify(job["candidate_revision"])
    plan_ref = next(r for r in contract["inputs"] if r["id"] == "grammar-gate-plan")
    plan = load(plan_ref["path"])
    for row in contract["inputs"] + plan["runtime_files"] + load(RESULT + "artifacts.json")["files"]:
        verify(row)
    assert plan["resources"] == {k: job["resource_budget"][k] for k in plan["resources"]}
    assert guard["cgroup"]["inode"] == job["execution_resources"]["cgroup_inode"]
    source_sets = {
        "P_encode": [gate.PLAIN, "tools/dualstream_grammar_v1.py"],
        "P_encode_decode": [gate.PLAIN, gate.DECODER, "tools/dualstream_grammar_v1.py"],
        "K_D_encode_decode": [gate.CODEC, "tools/dualstream_grammar_v1.py"],
        "union": gate.PACKAGE,
    }
    inventories = {}
    for name, paths in source_sets.items():
        files = [dict(**ref(path), bytes=(ROOT / path).stat().st_size) for path in paths]
        inventories[name] = dict(files=files, bytes=sum(r["bytes"] for r in files),
            accounting="Uncompressed local source inventory for exact invoked commands, not complete counted package.")
    assert inventories["P_encode_decode"]["bytes"] == 33804
    assert inventories["K_D_encode_decode"]["bytes"] == 35943
    assert inventories["union"]["bytes"] == 41941
    revision = dict(candidateId=CID, candidateTreeSha256=job["candidate_tree_sha256"], receipt=job["candidate_revision"])
    outputs = {}
    index = dict(schema="gamma.enwiki9.terminal-result-index.v1", job=ref(job_path), guard=ref(guard_path), arms=[],
                 evidence=[ref(RESULT + "stage-decision.json"), ref(RESULT + "costs-table.json")])
    raw_path = plan["population"]["path"]
    raw = (ROOT / raw_path).read_bytes()
    for row in stage["arms"]:
        arm = row["arm"]["id"]
        for artifact in row["artifacts"].values():
            verify(artifact)
        archive, inverse, repeat = [(ROOT / row["artifacts"][key]["path"]).read_bytes() for key in ("archive", "restored", "repeat")]
        assert inverse == raw and archive == repeat and len(archive) == row["archive_bytes"] == sum(row["accounting"].values())
        executions = [load(RESULT + arm + "-" + phase + ".execution.json") for phase in ("encode", "decode", "repeat")]
        assert executions == [p for p in stage["commands"] if p["phase"].startswith(arm + "-")]
        assert Path(executions[2]["argv"][3]) == ROOT / row["artifacts"]["restored"]["path"]
        assert executions[2]["argv"][2] == "encode"
        for execution in executions:
            mode = "decode" if execution["phase"].endswith("-decode") else "encode"
            tool = (gate.PLAIN if mode == "encode" else gate.DECODER) if arm == "P" else gate.CODEC
            assert Path(execution["argv"][1]) == ROOT / tool and execution["argv"][2] == mode
            events = [r["event"] for r in guard["phase_markers"] if r["phase"] == execution["phase"]]
            assert events == ["start", "end"]
        encoded, decoded, repeated = [load(RESULT + arm + "-" + phase + ".stdout") for phase in ("encode", "decode", "repeat")]
        actual_costs, actual_frames = gate.checked_report(encoded["result"], row["arm"], ROOT / row["artifacts"]["archive"]["path"], plan, raw)
        assert actual_costs == row["accounting"] and actual_frames == row["frames"]
        assert encoded["result"] == repeated["result"]
        if arm != "P":
            assert gate.common_report(encoded["result"]) == gate.common_report(decoded["result"])
        result = dict(schema="gamma.enwiki9.driver-result.v2", program_id=CID, program_name="Causal-bucket codec " + arm,
            arm=arm, candidate_revision=revision, objective=contract["objective"], timestamp=job["finished_at"],
            run_source=job_path, run_purpose="diagnostic", run_scope_label="opening250KB-causal-bucket-" + arm,
            run_tags=["causal-bucket", "raw-transform", "diagnostic", arm], data_path=raw_path, data_size=len(raw),
            data_sha256=hashlib.sha256(raw).hexdigest(), data_md5=hashlib.md5(raw).hexdigest(),
            compressed_size=len(archive), compressed_sha256=hashlib.sha256(archive).hexdigest(), compressed_md5=hashlib.md5(archive).hexdigest(),
            bits_per_byte=8 * len(archive) / len(raw), program_size=None, hutter_score=None,
            hutter_score_kind="diagnostic-causal-bucket-grammar", complete_package_bytes=None, full_corpus_score_bytes=None,
            prize_claimable=False, score_accounting_complete=False, resource_evidence_complete=False,
            qualification_status="not-certified", execution_mode="discovery", timing_authority="diagnostic", roundtrip_ok=True,
            determinism=dict(scope="single-host", single_host_byte_equal=True), raw_encoder_repeat_proved=True,
            repeat_scope="raw-transform-and-encoding", compress_time_s=encoded["elapsed_seconds"], decompress_time_s=decoded["elapsed_seconds"],
            encoding_cpu_seconds=encoded["cpu_seconds"], decoding_cpu_seconds=decoded["cpu_seconds"], repeat_time_s=repeated["elapsed_seconds"],
            run_time_s=sum(p["elapsed_seconds"] for p in stage["commands"] if p["phase"].startswith(arm + "-")),
            run_time_scope="Raw encoding, independent decoding and renewed raw encoding with the same fixed transform.",
            memory_kib=dict(peak=max(p["peak_process_rss_kib"] for p in (encoded, decoded, repeated))),
            host=dict(machine=platform.machine(), node=platform.node(), python=platform.python_version(), system=platform.system()),
            accounting=row["accounting"], artifacts=row["artifacts"],
            local_source_inventory=inventories["P_encode_decode" if arm == "P" else "K_D_encode_decode"],
            selected_frames=row["selected_frames"],
            missing_diagnostics=job["execution_resources"]["missing_diagnostics"], closed_guard=ref(guard_path), closed_job=ref(job_path),
            source_arm_result=ref(RESULT + arm + ".result.json"),
            run_context="Stable predecessor-byte FIFO transform with strict complete-frame admission; P/K identical. Package qualification unknown.",
            deterministic_repeat=dict(single_host_byte_equal=True, selection_repeated=arm != "P",
                first_run_sha256=hashlib.sha256(archive).hexdigest(), second_run_sha256=hashlib.sha256(repeat).hexdigest(),
                first_run_md5=hashlib.md5(archive).hexdigest(), second_run_md5=hashlib.md5(repeat).hexdigest(), first_divergence_byte=None))
        out = DEST + "/normalized/" + arm + ".json"
        outputs[out] = result
        data = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
        index["arms"].append(dict(arm=arm, result=dict(path=out, sha256="sha256:" + hashlib.sha256(data).hexdigest()), artifacts=row["artifacts"]))
    assert {r["arm"]["id"] for r in stage["arms"]} == {"P", "K", "D"}
    assert (ROOT / RESULT / "P.d2g").read_bytes() == (ROOT / RESULT / "K.d2g").read_bytes() == (ROOT / RESULT / "D.d2g").read_bytes()
    costs = stage["costs"]
    assert gate.comparison_table(stage["arms"], plan) == costs == load(RESULT + "costs-table.json")
    by_arm = {r["arm"]["id"]: r for r in stage["arms"]}
    frame_comparisons = []
    for i, (k, d) in enumerate(zip(by_arm["K"]["frames"], by_arm["D"]["frames"], strict=True)):
        assert k["comparison"] == d["comparison"]
        c = d["comparison"]
        assert c["selected"] is False and c["delta"] == c["plain_bytes"] - c["bucket_bytes"] < 0
        frame_comparisons.append(dict(frame=i, raw_bytes=d["raw_bytes"], raw_sha256=d["raw_sha256"], **c))
    assert [r["delta"] for r in frame_comparisons] == [-11850, -11964, -9165, -8303]
    forced_total = gate.driver.codec.HEADER.size + sum(r["bucket_bytes"] for r in frame_comparisons)
    assert forced_total == 130323
    rejected_transform = dict(frame_comparisons=frame_comparisons,
        forced_candidate_cost_sum_bytes=forced_total, unchanged_plain_archive_bytes=costs["archive_bytes"]["P"],
        forced_candidate_cost_sum_growth_bytes=forced_total - costs["archive_bytes"]["P"],
        full_forced_archive_retained=False,
        scope="Sum of measured rejected independent frame sizes plus common header; no retained forced full archive or extra encode is claimed.")
    assert len(raw) == 250000 and costs["archive_bytes"] == {"P": 89041, "K": 89041, "D": 89041}
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
    outputs[DEST + ".json"] = dict(schema="gamma.enwiki9.causal-bucket-terminal.v1", candidate_id=CID,
        job=ref(job_path), guard=ref(guard_path), experiment=ref(contract_path), stage=ref(RESULT + "stage-decision.json"),
        measurements=measurements, costs=costs,
        gate_resources=dict(elapsed_seconds=guard["elapsed_s"], peaks=guard["peaks"], samples=guard["sample_count"], guards=guard["guards"]),
        selected_frames={r["arm"]["id"]:r["selected_frames"] for r in stage["arms"]},
        rejected_transform=rejected_transform, source_inventories=inventories,
        D_minus_P_local_source_bytes=inventories["K_D_encode_decode"]["bytes"] - inventories["P_encode_decode"]["bytes"],
        route="Eligible for separately frozen fresh confirmation" if costs["strict_d_improvement"] else "Park this realization; fallback equality grants no confirmation",
        limits=["No full-corpus score or projection.",
                "All corpus frames use plain fallback; no transformed corpus payload was selected.",
                "Rejected transformed frame costs are measured but their full forced archive is not retained.",
                "Runtime/source/license/options qualification remains unresolved; source inventory differences are not counted package gains.",
                "The decoder inflates and follows FIFO queues; no recompression, novelty or smallest-decoder claim.",
                "This fixed predecessor-byte transform with Deflate is rejected on this population, not all reversible order transforms."],
        full_corpus_score_bytes=None, complete_package_bytes=None, objective_credit_bytes=0)
    print(json.dumps({path:json.dumps(value, indent=2, sort_keys=True) + "\n" for path,value in outputs.items()}))


if __name__ == "__main__":
    main()
