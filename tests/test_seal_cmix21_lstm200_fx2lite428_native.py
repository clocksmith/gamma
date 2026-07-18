from projects.enwiki9.tools.seal_cmix21_lstm200_fx2lite428_native import (
    calculate_economics,
    clean_tree_guard,
)


def test_calculate_economics_preserves_conservative_floor() -> None:
    economics = calculate_economics(
        geometry_archive_10m=1_643_626,
        compact_archive_10m=1_637_513,
        compact_package_bytes=264_314,
        candidate_package_bytes=347_170,
        endpoint_full_saved_bytes=272,
        endpoint_holdout_rate_bytes_per_1m=260.0,
    )

    assert economics["direct_term_forecast_score_bytes"] == 109_461_979
    assert economics["conservative_required_endpoint_gain_bytes_1g"] == 237_179
    assert economics["conservative_full_forecast_score_bytes"] == 109_465_179
    assert economics["conservative_full_forecast_margin_bytes"] == 34_821
    assert economics["conservative_holdout_forecast_score_bytes"] == 109_477_179
    assert economics["conservative_holdout_forecast_margin_bytes"] == 22_821
    assert economics["full_and_holdout_forecasts_below_target"] is True


def test_clean_tree_guard_requires_aggregate_decimal_compliance() -> None:
    guard = {
        "status": "complete",
        "returncode": 0,
        "limit_mode": "tree",
        "rss_guard_exceeded": False,
        "official_decimal_limit_kib": 9_765_625,
        "official_decimal_over_limit_kib": 0,
        "max_sampled_tree_rss_kib": 9_045_752,
    }

    assert clean_tree_guard(guard) is True
    assert clean_tree_guard({**guard, "limit_mode": "max_single"}) is False
    assert clean_tree_guard(
        {**guard, "max_sampled_tree_rss_kib": 9_765_626}
    ) is False
