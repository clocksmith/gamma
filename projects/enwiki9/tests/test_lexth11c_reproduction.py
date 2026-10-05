import struct
import pytest

from gamma_enwiki9.adapters.lexth11c_reproduction import accounting, donor_sandbox, layout


def files():
    header = struct.pack("<4i", 3, 5, 0, 7)
    compressor = b"ELF-stub" + b"dic" + b"order" + b"weights" + header
    archive = b"ELF-stub" + b"dic" + b"weights" + b"payload!!" + struct.pack("<4i", 3, 5, 9, 7)
    return compressor, archive


def test_two_copy_accounting_and_omitted_archive_order():
    c, a = files()
    score = accounting(c, a, 12)
    assert score["A"] == 9 and score["W"] == 7
    assert score["S"] == score["A"] + 2 * score["W"] + score["C"] == len(c) + len(a) + 12
    assert score["archive"]["order_bytes"] == 0
    assert score["compressor"]["order_bytes"] == 5


def test_differing_paid_weight_copy_rejected():
    c, a = files()
    with pytest.raises(ValueError, match="weight copies"):
        accounting(c, a.replace(b"weights", b"changed"), 12)


@pytest.mark.parametrize("data", [b"", struct.pack("<4i", -1, 0, 0, 1), struct.pack("<4i", 10, 20, 0, 30)])
def test_invalid_layout(data):
    with pytest.raises(ValueError):
        layout(data, archive=False)


@pytest.mark.parametrize("options", [None, -1, True])
def test_missing_or_invalid_options_rejected(options):
    with pytest.raises(ValueError):
        accounting(*files(), options)


def test_decode_sandbox_has_no_corpus_or_source_mount(tmp_path):
    runtime = {"bwrap": {"resolved_path": "/usr/bin/bwrap"}, "providers": {
        "ld-linux-x86-64.so.2": {"resolved_path": "/provider/ld.so"}},
        "shell": {"resolved_path": "/provider/dash"}}
    command = donor_sandbox(runtime, tmp_path)
    assert "--unshare-all" in command
    assert command[-2:] == ["--", "./archive9"]
    assert "/input" not in command
    assert "/provider/dash" in command
    assert str(tmp_path) in command
