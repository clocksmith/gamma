from projects.enwiki9.tools.seal_cmix21_lstm200_fx2lite428_10m_codec_failure import (
    last_progress_percent,
    require_nonmemory_codec_failure,
)


def test_last_progress_percent_uses_terminal_sample() -> None:
    assert last_progress_percent("progress: 40.48%\rprogress: 40.49%") == 40.49


def test_nonmemory_failure_rejects_rss_breach() -> None:
    guard = {
        "status": "complete",
        "returncode": 1,
        "limit_mode": "tree",
        "rss_guard_exceeded": False,
        "official_decimal_over_limit_kib": 0,
        "max_sampled_tree_rss_kib": 9_071_128,
        "official_decimal_limit_kib": 9_765_625,
    }
    require_nonmemory_codec_failure(guard)
    try:
        require_nonmemory_codec_failure({**guard, "rss_guard_exceeded": True})
    except RuntimeError:
        pass
    else:
        raise AssertionError("RSS breach was accepted as a codec-only failure")
