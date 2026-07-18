from projects.enwiki9.tools.seal_cmix21_lstm200_fx2lite428_ppmd_recovery import (
    calculate_repaired_economics,
)


def test_v7_package_restores_original_strict_10m_ceiling() -> None:
    economics = calculate_repaired_economics(
        prior_economics={
            "candidate_source_package_bytes": 347_170,
            "conservative_required_endpoint_gain_bytes_1g": 237_179,
            "compact_archive_bytes_10m": 1_637_513,
            "projected_endpoint_full_gain_bytes_1g": 272_000,
            "endpoint_holdout_saved_bytes_per_1m": 260.0,
        },
        repaired_package_bytes=347_183,
    )

    assert economics["source_package_increase_bytes"] == 13
    assert economics["conservative_required_endpoint_gain_bytes_1g"] == 237_192
    assert economics["conservative_required_endpoint_gain_bytes_10m"] == 2_372
    assert economics["strict_candidate_archive_ceiling_bytes_10m"] == 1_635_141
    assert economics["conservative_holdout_forecast_margin_bytes"] == 22_808
