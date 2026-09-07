"""Build prospective metadata in stdout; never open retained corpus payloads."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "tools"))
import fx2_causal_field_preceding_gate_v2 as gate

def ref(name):
    data = (ROOT / name).read_bytes()
    return {"path": name, "bytes": len(data),
            "sha256": "sha256:" + hashlib.sha256(data).hexdigest()}

stamp = datetime.now(timezone.utc).isoformat()
unit_name = "operations/evidence/20260907_fx2_causal_preceding_integration_unit.json"
plan_name = "operations/provenance/" + gate.ID + "_execution.json"
old = json.loads((ROOT / "operations/adaptive/experiments/fx2_causal_field_wrt_replay250k_q0_v1.json").read_text())
old_plan = json.loads((ROOT / "operations/provenance/fx2_causal_field_wrt_replay250k_q0_v1_execution.json").read_text())
audit = json.loads((ROOT / gate.AUDIT).read_text())
reflection_name = "operations/adaptive/reflections/20260907T141904Z_b82cd55283.json"
reflection = json.loads((ROOT / reflection_name).read_text())
parent = {"candidateId": reflection["candidateId"], "revision": reflection["candidateRevision"]["receipt"]}
package = [ref(name) for name in [gate.CORE, *gate.DYNAMIC_SOURCES]]
package_bytes = sum(row["bytes"] for row in package)
antecedent_names = [
    unit_name, "operations/provenance/fx2_causal_preceding_wrt250k_q0_v1_plan.json",
    "operations/provenance/public_fx2_gcc15_toolchain_20260905.json",
    reflection_name, parent["revision"]["path"], reflection["experiment"]["path"],
    "operations/provenance/fx2_causal_field_opportunity_terminal_20260907.json",
]
antecedents = [ref(name) for name in antecedent_names]
plan = {
    "schema": "gamma.enwiki9.fx2-causal-preceding-execution.v1",
    "candidate_id": gate.ID, "owner": "root_explore", "created_at": stamp,
    "resources": gate.CAPS,
    "phase_limits": {"threads": 1, "address_space_bytes": 536870912, "cpu_seconds": 60,
                     "file_bytes": 33554432, "wall_seconds": 180,
                     "stop": "Aggregate900 wall seconds, each phase180 wall/60CPU; no automatic retries or larger population."},
    "python_executable": old_plan["python_executable"], "runtime_files": old_plan["runtime_files"],
    "local_package_files": package,
    "population": {**{k: row[0] for k, row in gate.POPULATION.items()},
                   "raw_bytes": 250000, "modeled_bytes": 151210, "raw_offset": 0,
                   "coordinate": "Retained modeled WRT bytes including mode byte7; big-endian modeled bits map one-to-one to retained Q16. No reprocessing of the prior truth trace.",
                   "selection": "One frozen configuration on already examined opening[0,250000). Later validation and confirmation remain sealed.",
                   "causal_warmup": "Empty field history; train associations only from completed valid invocations in this population."},
    "antecedents": antecedents,
    "measured_kernels": {
        "unit_receipt": ref(unit_name), "author_tests": 13, "runner_tests": 24,
        "author_fixture_raw_bytes": 132, "runner_fixture_raw_bytes": 84,
        "runner_test_wall_seconds": 2.256841397844255,
        "runner_test_aggregate_child_cpu_seconds": 1.270894, "runner_test_peak_rss_kib": 37360,
        "prior_same_population_receipt": ref(gate.AUDIT),
        "prior_same_population_five_arm_wall_seconds": 65.8108,
        "prior_same_population_cgroup_peak_bytes": 185974784,
        "resource_rationale": "Six finite replays of1209680 modeled bits; FIFO128 and bounded256-byte donors. Reuse verified Q16 avoids model inference and the truth-bearing trace. Stops are limits, not duration predictions.",
        "timing_authority": "shared-host diagnostic"},
    "arms": {
        "P": "Original baseP with unchanged parent Q16 and native framing.",
        "K": "Adjacent bookkeeping with zero injection; exact P probabilities/archive.",
        "T": "Immediately preceding completed-field coordinate with the sealed integer posterior.",
        "O": "Original baseT first-field selector; exact previous T archive/probabilities and every-byte state chain.",
        "R": "Compatible same-template/target recency from the adjacent table.",
        "S": "Rotated compatible adjacent association; abstain without exact tuple and alternatives."},
    "validation": {
        "independent_processes": 18, "operations": list(gate.PHASES),
        "required_active": ["T", "R", "S"], "original_O_activity_reported_separately": True,
        "mandatory": ["Every arm exact raw inverse, repeat archive, complete state/probability and per-byte synchronization agreement.",
                      "P/K preserve native parent payload; O preserves sealed original first-field T evidence.",
                      "Authenticated retained raw/modeled/Q16/dictionary/projection; no truth-trace reprocessing.",
                      "Closed continuous resource evidence and source/artifact authentication precede decision publication."],
        "scientific_success": "T archive strictly smaller than P/O/R/S with active T/R/S; conditional predictive value only.",
        "failure_classes": ["implementation_or_evidence_failure", "budget_exhaustion",
                            "inconclusive_inactive_opportunities_or_controls",
                            "failed_causal_controls", "weak_compression"],
        "no_automatic_larger_gate": True},
    "accounting": {
        "local_source_bytes": package_bytes, "decoder_arm_option_bytes_per_archive": 1,
        "native_framing_bytes": 46, "external_q16_bytes": 2419360,
        "external_dictionary_bytes": 411996, "complete_package_bytes": None,
        "full_corpus_score_bytes": None, "objective_credit_bytes": 0,
        "objective_complete_bytes": 99000000,
        "unresolved": ["Standalone native parent prediction", "Complete runtime and license distribution",
                       "Native specialist package cost", "Independent qualifying resources and distant/full transfer"]},
    "implementation_history": {
        "active_runner": gate.SELF, "superseded_runner": "tools/fx2_causal_field_preceding_gate_v1.py",
        "v1_result": "Synthetic codec phases passed; one missing-source test received a fail-closed KeyError instead of expected ValueError. Preserve v1 and attempt_01.",
        "v2_delta": "Explicit missing-source failure, reserved-population pre-admission read rejection, tested canonical guard command helper. No codec/selector mutation.",
        "standing_ownership": "Published integration plan owns this independent lane; v2 replaces only the unqueued runner implementation."},
    "execution_policy": "Publish source, review, input contract and ownership; queue held and publish its exact claim before releasing on fresh admission. CPU2, no installation, HORIZON and MIDAS untouched."}
plan_bytes = (json.dumps(plan, indent=2, sort_keys=True) + "\n").encode()
plan_ref = {"path": plan_name, "bytes": len(plan_bytes), "sha256": "sha256:" + hashlib.sha256(plan_bytes).hexdigest()}
names = {r["path"] for r in old["inputs"] if r["path"].startswith(("contracts/", "lib/"))}
names.update([gate.SELF, gate.CORE, *gate.DYNAMIC_SOURCES,
              "tools/enwiki9_lab.py", "tools/enwiki9_python_source_closure.py",
              "tools/research_contracts.py", "tools/run_with_resource_guard_v3.py",
              "tests/test_fx2_causal_field_preceding_gate_v2.py",
              "tests/test_fx2_causal_field_preceding_replay_v1.py", gate.AUDIT, gate.REFLECTION,
              *antecedent_names, *(audit[k]["path"] for k in ("job", "guard", "decision"))])
inputs = [ref(name) for name in sorted(names)]
inputs += [{"path": name, "bytes": size, "sha256": "sha256:" + value}
           for name, size, value in gate.POPULATION.values()]
inputs.append(plan_ref)
special_ids = {gate.SELF: "runner", gate.CORE: "codec", plan_name: gate.PLAN_ID, unit_name: "gate-unit"}
inputs = [{**row, "id": special_ids.get(row["path"], "frozen-input-" + str(i).zfill(3))}
          for i, row in enumerate(sorted(inputs, key=lambda r: r["path"]))]
contract = copy.deepcopy(old)
contract.update(experimentId=gate.ID, proposalId=gate.ID, parent=parent, generatedUtc=stamp,
    hypothesis={"claim": "Immediately preceding completed-field conditioning yields useful exact donor probabilities under the actual parent beyond the original first-field selector and matched adjacent controls.",
                "falsification": "One frozen development comparison; inactive T/R/S is inconclusive. With valid active controls, failure to beat P/O/R/S rejects this realization. Budget and implementation failures are separate. No extrapolated score or automatic scale."},
    changedMechanism="Replace only the original first-field conditioning coordinate with the immediately preceding completed-field coordinate. Retain FIFO128, parser/WRT alignment, calibration, integer mixture and finite coder. No fallback or additional specialist.",
    invariants=plan["validation"]["mandatory"] + [
        "All18 independent phases share frozen source, population and package accounting.",
        "Decoder receives archive, external Q16, dictionary and raw length/hash; no raw/modeled truth input.",
        "Only completed valid invocations train; predict before truth, observe after truth.",
        "T/R/S activity required; O inactivity alone does not invalidate matched active adjacent controls.",
        "CPU2 one thread,1GiB memory,zero swap,256MiB scratch,900wall aggregate; phase512MiBAS/60CPU/180wall/32MiBfile.",
        "99M complete engineering target; no full-corpus score or attribution to Gamma for upstream FX2.",
        "No model inference rerun, no dependency installation, no HORIZON/MIDAS changes or withheld data access."],
    controls=[{"id": arm, "role": "treatment" if arm == "T" else "shifted" if arm == "S" else "comparator",
               "definition": text} for arm, text in plan["arms"].items()],
    population={"unit": "WRT bit", "scopeBytes": 250000, "scopeSymbols": 1209680,
                "selection": plan["population"]["selection"], "coordinate": plan["population"]["coordinate"]},
    causalBoundary={"availableInformation": ["Retained verified pre-truth Q16 under identical frontend/source/state coordinates.",
                       "Earlier completed decoded WRT/raw events and valid field invocations; exact aligned donors and compatible entry state."],
                    "forbiddenInformation": ["Future field truths at prediction time or raw/modeled truth supplied to decoder.",
                        "Truth-trace reanalysis, model inference rerun, withheld populations, HORIZON/MIDAS state."]},
    inputs=inputs, budget={"expectedGrossSavingsBytes": 0, "maximumAddedPackageBytes": package_bytes + 1,
                         "expectedNetSavingsBytes": -(package_bytes + 1)})
for row in contract["measurements"]:
    row["definition"] = row["definition"].replace("All five", "All six").replace("all fifteen", "all eighteen").replace("five arms", "six arms").replace("All five required raw local source files", "Seven required raw local codec source files").replace("P, R and S", "P, O, R and S")
contract["measurements"] += [
    {"id": "original_first_field_identity_pass", "definition": "O preserves sealed original T archive/probability/state evidence.", "unit": "boolean"},
    {"id": "original_archive_bytes", "definition": "O native-framed archive bytes.", "unit": "bytes"},
    {"id": "decoder_arm_option_bytes", "definition": "Explicit one-byte arm option required for each decode invocation.", "unit": "bytes"}]
contract["outputs"] = ["results/" + gate.ID + "/" + name for name in gate.declared_outputs(inputs)]
contract["outputs"].append("results/" + gate.ID + "/decision.json")
print(json.dumps({"plan": plan, "contract": contract, "plan_ref": plan_ref}))
