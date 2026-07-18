from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


TOOLS = Path(__file__).resolve().parents[1] / "projects/enwiki9/tools"
sys.path.insert(0, str(TOOLS))
MODULE_PATH = TOOLS / "wrt_entity_regret_router_shadow.py"
SPEC = importlib.util.spec_from_file_location(
    "wrt_entity_regret_router_shadow", MODULE_PATH
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_router_uses_only_prior_completed_events() -> None:
    router = MODULE.NodeRegretRouter(minimum_observations=1, margin_qbits=0)

    assert router.active(7) is False
    router.update(7, gain_qbits=512, eligible_rows=8)
    assert router.active(7) is True

    # This loss is observed only after the routed event, then disables its successor.
    router.update(7, gain_qbits=-1024, eligible_rows=8)
    assert router.active(7) is False


def test_router_observation_floor_and_margin_are_strict() -> None:
    router = MODULE.NodeRegretRouter(
        minimum_observations=2, margin_qbits=256
    )
    router.update(3, gain_qbits=256, eligible_rows=1)
    assert router.active(3) is False
    router.update(3, gain_qbits=1, eligible_rows=1)
    assert router.active(3) is True


def test_ineligible_or_unknown_updates_do_not_create_state() -> None:
    router = MODULE.NodeRegretRouter(minimum_observations=0, margin_qbits=0)
    router.update(None, gain_qbits=1000, eligible_rows=8)
    router.update(4, gain_qbits=1000, eligible_rows=0)

    assert router.states == {}
    assert router.active(None) is False
    assert router.active(4) is False


def test_reflected_regret_can_recover_after_a_loss() -> None:
    router = MODULE.NodeRegretRouter(minimum_observations=1, margin_qbits=0)
    router.update(5, gain_qbits=-500, eligible_rows=1)
    assert router.states[5].reflected_wealth_qbits == 0
    assert router.active(5) is False

    router.update(5, gain_qbits=300, eligible_rows=1)
    assert router.states[5].reflected_wealth_qbits == 300
    assert router.active(5) is True
