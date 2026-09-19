"""The 95M-96M goal changes target bytes, never historical evidence or gates."""
import copy

import pytest

from projects.enwiki9.tools import research_contracts as contracts


def test_active_ceiling_and_stretch_target():
    contracts.validate_artifact(contracts.OBJECTIVE_PATH)
    objective = contracts.validate_objective()
    binding = contracts.objective_binding()
    assert binding["objectiveId"] == "gamma-enwiki9-hutter-96m-v4"
    assert binding["targetScoreBytes"] == 96_000_000
    assert objective["score"]["stretchTargetBytes"] == 95_000_000
    assert binding["corpusBytes"] == 1_000_000_000


@pytest.mark.parametrize("version,target,digest", [
    ("v1", 105_000_000, "ce4c435c0f398caf65a09050c8518d9c5ea63239f9156048ea2aaaf9b8ffa7e8"),
    ("v2", 99_000_000, "16badfa6c1a53b47bcc12b089fdd9c21f7405ea56a84344d60c28d2252da8288"),
    ("v3", 90_000_000, "e91ff20e92c3cac8acb0cbe5c79fc8e8a3b427d7e151245c8eecc52b1c32fa00"),
])
def test_old_targets_remain_bound_to_original_digests(version, target, digest):
    binding = contracts.objective_binding(objective_path=f"contracts/research/{version}/objective-contract.json")
    assert binding["targetScoreBytes"] == target
    assert binding["objectiveDigest"] == "sha256:" + digest
    contracts._validate_objective_binding(binding, "original")
    relabelled = copy.deepcopy(binding)
    relabelled["targetScoreBytes"] = 96_000_000
    with pytest.raises(ValueError):
        contracts._validate_objective_binding(relabelled, "relabelled")


def test_new_target_preserves_every_non_score_obligation():
    old = contracts.validate_objective(objective_path="contracts/research/v3/objective-contract.json")
    new = contracts.validate_objective()
    changed = {"schema", "version", "objectiveId", "effectiveUtc", "score", "migration"}
    assert {k: v for k, v in old.items() if k not in changed} == {
        k: v for k, v in new.items() if k not in changed}
    assert {k: v for k, v in old["score"].items() if k not in {"targetBytes", "targetMeaning"}} == {
        k: v for k, v in new["score"].items() if k not in {"targetBytes", "targetMeaning", "stretchTargetBytes"}}
    assert new["migration"]["previousObjectiveDigest"] == contracts.objective_binding(
        objective_path="contracts/research/v3/objective-contract.json")["objectiveDigest"]


def test_frontier_report_default_uses_active_target():
    from projects.enwiki9.tools import frontier_target_report as report
    assert report.DEFAULT_TARGET_PERCENT == 9.6
