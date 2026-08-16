#!/usr/bin/env python3
"""Freeze the joint open update, recurrent-state, and next-forward experiment."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from enwiki9_python_source_closure import local_source_closure
import research_contracts


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_update_forward_chain_64_q0_v1"
RUNNER = ROOT / "tools/nncp_open_profile_update_forward_chain_64_q0.py"
MATERIALIZER = Path(__file__).resolve()
PROGRAM = ROOT / "programs" / CANDIDATE_ID
OUTPUT = ROOT / f"operations/adaptive/experiments/{CANDIDATE_ID}.json"
PARENT_ID = "nncp_ggml_postupdate_forward_parity_64_q1_retry_v2"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reference(path: Path, identifier: str) -> dict[str, str]:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents or not resolved.is_file():
        raise ValueError(f"experiment input is not a project file: {path}")
    return {
        "id": identifier,
        "path": resolved.relative_to(ROOT.resolve()).as_posix(),
        "sha256": f"sha256:{sha256(resolved)}",
    }


def source_id(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    slug = "".join(character if character.isalnum() else "-" for character in relative)
    return f"runtime-source-{slug}-{sha256(path)[:12]}"


def measurement(identifier: str, unit: str, definition: str) -> dict[str, str]:
    return {"id": identifier, "unit": unit, "definition": definition}


def predicate(identifier: str, measurement_id: str, threshold: object) -> dict[str, object]:
    return {
        "id": identifier,
        "measurement": measurement_id,
        "operator": "eq",
        "threshold": threshold,
    }


def main() -> int:
    if OUTPUT.exists():
        raise ValueError(f"experiment already exists: {OUTPUT}")
    revisions = sorted(
        (ROOT / "operations/adaptive/candidate-revisions" / PARENT_ID).glob("*.json")
    )
    if not revisions:
        raise ValueError("parent candidate has no frozen revision")
    parent_revision = revisions[-1]
    named_inputs = [
        ("runner", RUNNER),
        ("materializer", MATERIALIZER),
        ("open-adam-payload-source", PROGRAM / "adam_payloads.cpp"),
        ("program-descriptor", PROGRAM / "program.py"),
        ("q3-update-decision", ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1/decision.json"),
        ("q3-update-manifest", ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1/fixture-manifest.json"),
        ("q3-update-guard", ROOT / "results/nncp_libnc_profile_update_fixture_64_q3_v1/guard.json"),
        ("q3-update-reflection", ROOT / "operations/adaptive/reflections/20260815T235124Z_86c7e4f805.json"),
        ("open-adam-decision", ROOT / "results/nncp_open_profile_adam_replay_64_q0_retry_v2/decision.json"),
        ("open-adam-reflection", ROOT / "operations/adaptive/reflections/20260816T003855Z_aab09244b0.json"),
        ("open-memory-decision", ROOT / "results/nncp_ggml_profile_memory_transition_64_q0_v1/decision.json"),
        ("open-memory-reflection", ROOT / "operations/adaptive/reflections/20260815T231108Z_4912fe7f1f.json"),
        ("preupdate-forward-decision", ROOT / "results/nncp_ggml_profile_forward_parity_64_qm18_v1/decision.json"),
        ("preupdate-forward-fixture", ROOT / "results/nncp_ggml_profile_forward_parity_64_qm18_v1/production_forward_fixture.tar.xz"),
        ("postupdate-forward-decision", ROOT / "results/nncp_ggml_postupdate_forward_parity_64_q1_retry_v2/decision.json"),
        ("postupdate-forward-reflection", ROOT / "operations/adaptive/reflections/20260816T021607Z_81c2c9ae94.json"),
        ("postupdate-forward-fixture", ROOT / "results/nncp_ggml_postupdate_forward_parity_64_q0_retry_v2/artifacts/production_forward_fixture.tar.xz"),
        ("exact-forward-source", ROOT / "results/nncp_ggml_postupdate_forward_parity_64_q1_retry_v2/ggml_profile_forward_source_closure.tar.xz"),
        ("open-adam-parent-source", ROOT / "programs/nncp_open_profile_adam_replay_64_q0_retry_v2/adam_replay.cpp"),
    ]
    inputs = [reference(path, identifier) for identifier, path in named_inputs]
    present = {row["path"] for row in inputs}
    for path in sorted(
        set(local_source_closure((RUNNER, MATERIALIZER))),
        key=lambda item: item.relative_to(ROOT).as_posix(),
    ):
        relative = path.relative_to(ROOT).as_posix()
        if relative not in present:
            inputs.append(reference(path, source_id(path)))
            present.add(relative)

    measurements = [
        measurement("antecedentsPass", "boolean", "Every promoted open update, memory, and exact-forward antecedent remains digest-bound and valid."),
        measurement("updateFixtureIdentityPass", "boolean", "The complete retained initial-parameter, optimizer, gradient, and state fixture matches its Q3 aggregate digest."),
        measurement("openAdamExact", "boolean", "Both fresh open Adam executions exactly match every retained comparator word."),
        measurement("openParameterPayloadCount", "parameter tensors", "Fresh parameter payloads generated from initial parameters, optimizer state, and gradients."),
        measurement("openParameterPayloadMismatchCount", "parameter tensors", "Generated parameter payloads whose digest differs from the retained post-update comparator."),
        measurement("openParameterDeterministic", "boolean", "Two fresh open Adam payload directories and reports are byte-identical."),
        measurement("preComparedTensorCount", "forward tensors", "Complete pre-update open-forward tensors compared to the retained oracle."),
        measurement("maximumPreTensorAbsoluteError", "float32 value", "Maximum complete pre-update tensor error in the first open execution."),
        measurement("maximumPreRepeatTensorAbsoluteError", "float32 value", "Maximum complete pre-update tensor error in the repeated open execution."),
        measurement("preForwardDeterministic", "boolean", "Two fresh pre-update open forwards emit byte-identical outputs."),
        measurement("openStateLayerCount", "recurrent layers", "Fresh recurrent-memory payloads generated by shift, append, and BF16 serialization."),
        measurement("openStateMismatchCount", "recurrent layers", "Generated recurrent-memory payloads whose digest differs from the retained post-update comparator."),
        measurement("openStateDeterministic", "boolean", "Two fresh open forward-to-memory transitions emit identical payload digests."),
        measurement("incumbentPostupdateContainersRemoved", "boolean", "The monolithic incumbent post-update parameter and state containers were removed before the chained forward."),
        measurement("comparedTensorCount", "forward tensors", "Complete next-segment tensors compared after open payload injection."),
        measurement("maximumTensorAbsoluteError", "float32 value", "Maximum next-segment tensor error in the first chained execution."),
        measurement("maximumRepeatTensorAbsoluteError", "float32 value", "Maximum next-segment tensor error in the repeated chained execution."),
        measurement("branchRows", "integer branch counts", "Complete next-segment arithmetic-branch rows compared."),
        measurement("maximumBranchCountDifference", "integer probability counts", "Maximum next-segment branch-count error."),
        measurement("repeatMaximumBranchCountDifference", "integer probability counts", "Maximum repeated next-segment branch-count error."),
        measurement("topologyDisagreementCount", "tree fields", "Next-segment tree topology or symbol-order disagreements."),
        measurement("truthPathDisagreementCount", "truth bits", "Next-segment truth-path disagreements."),
        measurement("postForwardDeterministic", "boolean", "Two fresh chained next-segment forwards emit byte-identical outputs."),
        measurement("forbiddenDynamicDependencyCount", "dependencies", "Dynamic teacher, LibNC, GGML, CUDA, OpenMP, or BLAS dependencies in the built forward."),
        measurement("incrementalSourceBytes", "bytes", "Compressed dependency-closed joint orchestration and open-update source package."),
        measurement("guardedWorkRootPass", "boolean", "All generated payloads, extractions, builds, and open outputs remained under and were removed with the guarded work root."),
    ]
    expected = {
        "antecedentsPass": True,
        "updateFixtureIdentityPass": True,
        "openAdamExact": True,
        "openParameterPayloadCount": 246,
        "openParameterPayloadMismatchCount": 0,
        "openParameterDeterministic": True,
        "preComparedTensorCount": 244,
        "maximumPreTensorAbsoluteError": 0,
        "maximumPreRepeatTensorAbsoluteError": 0,
        "preForwardDeterministic": True,
        "openStateLayerCount": 20,
        "openStateMismatchCount": 0,
        "openStateDeterministic": True,
        "incumbentPostupdateContainersRemoved": True,
        "comparedTensorCount": 244,
        "maximumTensorAbsoluteError": 0,
        "maximumRepeatTensorAbsoluteError": 0,
        "branchRows": 896,
        "maximumBranchCountDifference": 0,
        "repeatMaximumBranchCountDifference": 0,
        "topologyDisagreementCount": 0,
        "truthPathDisagreementCount": 0,
        "postForwardDeterministic": True,
        "forbiddenDynamicDependencyCount": 0,
        "guardedWorkRootPass": True,
    }
    promotion = [
        predicate(f"p-{name.lower()}", name, threshold)
        for name, threshold in expected.items()
    ]
    promotion.append(
        {
            "id": "p-incrementalsourcebytes",
            "measurement": "incrementalSourceBytes",
            "operator": "lte",
            "threshold": 2_000_000,
        }
    )
    kill = [
        predicate("k-antecedents", "antecedentsPass", True),
        {"id": "k-parameter-mismatch", "measurement": "openParameterPayloadMismatchCount", "operator": "gt", "threshold": 0},
        {"id": "k-state-mismatch", "measurement": "openStateMismatchCount", "operator": "gt", "threshold": 0},
        {"id": "k-forward-mismatch", "measurement": "maximumTensorAbsoluteError", "operator": "gt", "threshold": 0},
    ]
    experiment = {
        "schema": "gamma.enwiki9.adaptive-experiment-contract.v1",
        "objective": research_contracts.objective_binding(),
        "experimentId": CANDIDATE_ID,
        "proposalId": CANDIDATE_ID,
        "status": "frozen",
        "registrationTiming": "prospective",
        "evidenceClass": "oracle",
        "objectiveCreditBytes": 0,
        "parent": {
            "candidateId": PARENT_ID,
            "revision": {
                "path": parent_revision.relative_to(ROOT).as_posix(),
                "sha256": f"sha256:{sha256(parent_revision)}",
            },
        },
        "hypothesis": {
            "claim": "A Gamma-authored open Adam update and open recurrent-memory transition, fed directly into the unchanged exact post-update forward, reproduce every retained next-segment tensor and arithmetic branch without consuming incumbent post-update parameter or memory payloads.",
            "falsification": "Any bound-input drift, generated parameter or memory mismatch, pre-forward error, next-forward tensor or branch error, replay difference, dependency violation, guard failure, or source overflow prevents promotion and forbids a causal open segment-transition claim.",
        },
        "changedMechanism": "Replace the retained incumbent-produced post-update parameter and recurrent-memory payloads with freshly generated outputs from the already proven open Adam and open shift-and-append mechanisms before running the unchanged exact next-segment forward.",
        "invariants": [
            "The Q3 initial parameters, optimizer state, named dense gradients, and pre-update recurrent state remain digest-bound oracle inputs.",
            "Open parameter payloads are written before final comparator containers are opened, and no retained final parameter word is copied into a generated payload.",
            "Open recurrent memory is derived only from pre-update BF16 memory and fresh exact pre-update forward attention inputs, then serialized with deterministic BF16 round-to-nearest-even.",
            "The incumbent post-update parameter and state containers are removed before the unchanged exact next-forward executable runs.",
            "Expected post-update payloads, tensors, and branch rows are comparator outputs only and never correction inputs.",
            "Both pre-update and next-segment forward paths execute twice, and all generated parameter, memory, tensor, and branch evidence must be exact.",
            "The closed teacher, LibNC, and NNCP are not executed during the retained replay.",
            "This experiment has zero objective credit: dense gradients remain teacher-captured, no open backward pass exists, and no archive, transfer, or full-corpus claim is authorized.",
        ],
        "controls": [
            {"id": "joint-open-chain", "role": "treatment", "definition": "Fresh Gamma open Adam payloads and fresh Gamma open recurrent-memory payloads are injected into the unchanged exact next-forward."},
            {"id": "retained-postupdate-oracle", "role": "comparator", "definition": "Digest-bound incumbent payloads, tensors, and branch rows are read only to score independently generated outputs."},
            {"id": "independent-open-replay", "role": "replay", "definition": "Every open generator and forward executes twice and must reproduce the same bytes."},
            {"id": "incumbent-splice-ban", "role": "negative", "definition": "The original monolithic post-update parameter and state containers are deleted, and every parameter and recurrent-memory payload is overwritten from a fresh open output before the next-forward."},
        ],
        "population": {
            "unit": "one complete production segment-transition payload, forward tensor element, or arithmetic-branch count",
            "scopeBytes": None,
            "scopeSymbols": 64,
            "selection": "All 246 parameter tensors, all 20 target-stream recurrent-memory layers, all 244 next-forward tensor groups, and all 896 next-segment branch rows at the first production update boundary.",
            "coordinate": "32-stream update [256,320), followed by target stream zero next-forward original-symbol coordinates [320,384).",
        },
        "causalBoundary": {
            "availableInformation": [
                "Digest-bound initial parameters, optimizer moments and low words, all named teacher-captured dense gradients, pre-update recurrent memory, pre-update inputs, next-segment inputs, fixed source, and frozen predicates.",
                "Retained final payloads and next-forward outputs only after each corresponding open payload or forward output has been completely generated.",
            ],
            "forbiddenInformation": [
                "Calling LibNC or NNCP, copying any incumbent post-update parameter or recurrent-memory payload into the open input, or fitting a correction to expected outputs.",
                "Claiming open backward generation, recursive training, compression gain, transfer, package viability, or Hutter objective credit.",
            ],
        },
        "inputs": inputs,
        "outputs": [
            f"results/{CANDIDATE_ID}/decision.json",
            f"results/{CANDIDATE_ID}/chain-receipt.json",
            f"results/{CANDIDATE_ID}/execution.json",
            f"results/{CANDIDATE_ID}/incremental_source.tar.xz",
        ],
        "measurements": measurements,
        "promotionPredicates": promotion,
        "killPredicates": kill,
        "budget": {
            "expectedGrossSavingsBytes": 0,
            "maximumAddedPackageBytes": 2_000_000,
            "expectedNetSavingsBytes": -2_000_000,
        },
        "search": {
            "expectedTransferRetention": 1.0,
            "expectedRuntimeRatio": 1.0,
            "expectedMemoryRatio": 1.0,
            "uncertaintyRisk": 0.1,
            "interactionRisk": 0.2,
        },
        "generatedUtc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "outputManifestPolicy": "complete-result-artifacts-v1",
        "pythonSourceClosureEntries": ["runner", "materializer"],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(experiment, indent=2, sort_keys=True) + "\n")
    try:
        research_contracts.validate_artifact(OUTPUT)
    except Exception:
        OUTPUT.unlink(missing_ok=True)
        raise
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
