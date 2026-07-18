from projects.enwiki9.tools.seal_cmix21_lstm200_fx2lite428_stats_failure import (
    parse_kernel_fault,
    peak_process_pid,
)


def test_peak_process_pid_selects_compressor() -> None:
    guard = {
        "peak_sample": {
            "processes": [
                {"pid": 10, "rss_kib": 4_000},
                {"pid": 11, "rss_kib": 9_000_000},
            ]
        }
    }
    assert peak_process_pid(guard) == 11


def test_parse_kernel_fault_uses_exact_pid_and_offset() -> None:
    text = (
        "2026-07-15 kernel: cmix[1902157]: segfault at 72b7936d35f0 "
        "ip 0000582b76732e20 in cmix[84e20,582b766c6000+12c000]\n"
    )
    line, offset = parse_kernel_fault(text, 1_902_157)
    assert "cmix[1902157]" in line
    assert offset == 0x84E20
