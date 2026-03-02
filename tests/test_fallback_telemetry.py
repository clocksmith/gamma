"""Regression tests for fallback telemetry accounting and logging."""

from __future__ import annotations

import logging

import pytest

from src.core.fallback_telemetry import FallbackTelemetry


@pytest.mark.regression
def test_fallback_telemetry_counts_increment() -> None:
    logger = logging.getLogger("tests.fallback_telemetry")
    tel = FallbackTelemetry("unit", logger)

    assert tel.record("alpha") == 1
    assert tel.record("alpha") == 2
    assert tel.record("beta") == 1
    assert tel.snapshot() == {"alpha": 2, "beta": 1}


@pytest.mark.regression
def test_fallback_telemetry_snapshot_is_copy() -> None:
    logger = logging.getLogger("tests.fallback_telemetry")
    tel = FallbackTelemetry("unit", logger)
    tel.record("alpha")

    snap = tel.snapshot()
    snap["alpha"] = 999

    assert tel.snapshot()["alpha"] == 1


@pytest.mark.regression
def test_fallback_telemetry_logs_exception(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("tests.fallback_telemetry")
    tel = FallbackTelemetry("unit", logger)

    with caplog.at_level(logging.WARNING):
        try:
            raise ValueError("boom")
        except ValueError as exc:
            count = tel.record("explode", exc, level=logging.WARNING)

    assert count == 1
    assert "unit fallback 'explode'" in caplog.text
    assert "ValueError" in caplog.text
