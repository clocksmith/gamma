from projects.enwiki9.tools.seal_endpoint428_pair_layer0_native import (
    add_disjoint_economics,
    calculate_economics,
)


def test_calculate_economics_uses_counted_source_delta() -> None:
    economics = calculate_economics(
        base_program_bytes=349_195,
        candidate_program_bytes=350_942,
        prefix_gain_bytes=67,
    )

    assert economics["incremental_program_bytes"] == 1_747
    assert economics["provisional_prefix_forecast_score_bytes"] == 109_492_151
    assert economics["provisional_prefix_forecast_margin_bytes"] == 7_849
    assert economics["required_exact_10m_gain_bytes"] == 884
    assert economics["maximum_exact_10m_archive_bytes"] == 1_634_811

    add_disjoint_economics(economics, disjoint_gain_bytes=89)
    assert economics["provisional_disjoint_forecast_score_bytes"] == 109_470_151
    assert economics["provisional_disjoint_forecast_margin_bytes"] == 29_849
