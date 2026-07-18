from projects.enwiki9.tools.seal_cmix21_lstm200_fx2lite428_10m import (
    calculate_10m_economics,
)


RECOVERY_ECONOMICS = {
    "conservative_required_endpoint_gain_bytes_1g": 237_474,
    "strict_candidate_archive_ceiling_bytes_10m": 1_635_138,
}


def test_10m_economics_passes_at_exact_fail_closed_ceiling() -> None:
    economics = calculate_10m_economics(
        base_archive_bytes=1_637_513,
        candidate_archive_bytes=1_635_138,
        recovery_economics=RECOVERY_ECONOMICS,
    )

    assert economics["gross_saved_bytes_10m"] == 2_375
    assert economics["projected_endpoint_gain_bytes_1g"] == 237_500
    assert economics["conservative_projected_margin_bytes"] == 26
    assert economics["strict_10m_economics_pass"] is True


def test_10m_economics_retires_one_byte_above_ceiling() -> None:
    economics = calculate_10m_economics(
        base_archive_bytes=1_637_513,
        candidate_archive_bytes=1_635_139,
        recovery_economics=RECOVERY_ECONOMICS,
    )

    assert economics["archive_ceiling_margin_bytes"] == -1
    assert economics["conservative_projected_margin_bytes"] == -74
    assert economics["strict_10m_economics_pass"] is False
