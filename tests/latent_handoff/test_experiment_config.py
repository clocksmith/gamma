from pathlib import Path

import pytest

from src.mind_meld.latent_handoff.contract import ContractError
from src.mind_meld.latent_handoff.experiment import load_config


CONFIG = Path("configs/latent_handoff/qwen3_0_6b_to_1_7b.yaml")


def test_checked_in_config_has_pinned_policy() -> None:
    config = load_config(CONFIG, require_materialized=False)
    assert len(config["source"]["revision"]) == 40
    assert len(config["target"]["revision"]) == 40
    assert config["runtime"]["attentionImplementation"] == "eager"
    assert config["runtime"]["deterministicAlgorithms"] is True
    assert config["phase1Receipts"] == {"source": None, "target": None}


def test_unmaterialized_config_fails_before_model_loading() -> None:
    with pytest.raises(ContractError, match="source.localPath is unset"):
        load_config(CONFIG)
