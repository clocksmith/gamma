from projects.enwiki9.tools.seal_endpoint428_pair_layer0_10m import (
    calculate_economics,
)


def economics(candidate_archive_bytes: int) -> dict[str, object]:
    return calculate_economics(
        base_archive_bytes=1_635_695,
        candidate_archive_bytes=candidate_archive_bytes,
        base_forecast_score_bytes=109_557_404,
        incremental_program_bytes=1_747,
        calibration_factor=66.955334,
        required_gain_bytes=884,
        archive_ceiling_bytes=1_634_811,
    )


def test_exact_ceiling_passes_with_conservative_projection() -> None:
    result = economics(1_634_811)
    assert result["saved_bytes_10m"] == 884
    assert result["economics_pass"] is True
    assert result["conservative_provisional_score_bytes"] == 109_499_963
    assert result["provisional_target_margin_bytes"] == 37


def test_one_byte_above_ceiling_fails() -> None:
    result = economics(1_634_812)
    assert result["saved_bytes_10m"] == 883
    assert result["economics_pass"] is False
    assert result["archive_ceiling_margin_bytes"] == -1
