from projects.enwiki9.tools.seal_cmix21_lstm200_fx2lite428_ppmd_recovery import (
    calculate_repaired_economics,
    clean_tree_guard,
)


def test_repaired_economics_charge_package_and_round_ceiling_fail_closed() -> None:
    economics = calculate_repaired_economics(
        prior_economics={
            "candidate_source_package_bytes": 347_170,
            "conservative_required_endpoint_gain_bytes_1g": 237_179,
            "compact_archive_bytes_10m": 1_637_513,
            "projected_endpoint_full_gain_bytes_1g": 272_000,
            "endpoint_holdout_saved_bytes_per_1m": 260.0,
        },
        repaired_package_bytes=347_465,
    )

    assert economics["source_package_increase_bytes"] == 295
    assert economics["conservative_required_endpoint_gain_bytes_1g"] == 237_474
    assert economics["conservative_required_endpoint_gain_bytes_10m"] == 2_375
    assert economics["strict_candidate_archive_ceiling_bytes_10m"] == 1_635_138
    assert economics["conservative_full_forecast_margin_bytes"] == 34_526
    assert economics["conservative_holdout_forecast_margin_bytes"] == 22_526
    assert economics["full_and_holdout_forecasts_below_target"] is True


def test_clean_tree_guard_rejects_decimal_or_tree_breach() -> None:
    guard = {
        "status": "complete",
        "returncode": 0,
        "limit_mode": "tree",
        "rss_guard_exceeded": False,
        "official_decimal_limit_kib": 9_765_625,
        "official_decimal_over_limit_kib": 0,
        "max_sampled_tree_rss_kib": 9_059_812,
    }

    assert clean_tree_guard(guard) is True
    assert clean_tree_guard({**guard, "returncode": 1}) is False
    assert clean_tree_guard({**guard, "limit_mode": "max_single"}) is False
    assert clean_tree_guard(
        {**guard, "max_sampled_tree_rss_kib": 9_765_626}
    ) is False
