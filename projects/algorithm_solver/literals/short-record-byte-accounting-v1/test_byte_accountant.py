#!/usr/bin/env python3
"""Golden-byte accounting tests for short-record codecs.

    python3 -B test_byte_accountant.py                                  # plain run
    python3 -B -m pytest -p no:cacheprovider test_byte_accountant.py

Standard library only. The expected numbers come from golden/gold1/expected.json, written by hand
from the format in README.md. Nothing here imports a codec, a baseline harness or a scorer.
"""
from __future__ import annotations

import contextlib
import io
import json
import random
import shutil
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import byte_accountant as A  # noqa: E402

GOLD = HERE / 'golden' / 'gold1'
ARTIFACTS = GOLD / 'artifacts'
EXPECTED = json.loads((GOLD / 'expected.json').read_text(encoding='utf-8'))
TEST_RECORDS = [(GOLD / 'records' / f'r{i}.txt').read_bytes() for i in range(3)]
# Training records for the leakage guard. They share the dictionary's entries, not the test text.
TRAIN_RECORDS = [b'fn start() {}', b'fn stop() {}']


def _full_report() -> dict:
    """What an honest producer of the gold1 set reports (the hand numbers)."""
    return {'codec': 'gold1-reference', 'records': 3, 'bytes': dict(EXPECTED['bytes'])}


def _dropped(component: str) -> dict:
    """A report with one component left out of both the breakdown and the total."""
    rep = _full_report()
    n = rep['bytes'].pop(component)
    rep['bytes']['total'] -= n
    return rep


def _problems(report: dict, artifact_dir=ARTIFACTS, **kw) -> list[str]:
    return A.check_report(report, A.account(artifact_dir), **kw)


def _expect_error(fn, *args, **kw) -> str:
    try:
        fn(*args, **kw)
    except A.AccountingError as exc:
        return str(exc)
    raise AssertionError('expected AccountingError')


@contextlib.contextmanager
def _copy_of_set():
    with tempfile.TemporaryDirectory() as tmp:
        dst = Path(tmp) / 'artifacts'
        shutil.copytree(ARTIFACTS, dst)
        yield dst


def _decode_gold1(artifact_dir: Path, i: int) -> bytes:
    """Reference reader for gold1, written from the README format. Reads only the counted files."""
    header = (artifact_dir / 'header.bin').read_bytes()
    assert header[:4] == b'GLD1' and header[4] == 1
    n_records, n_entries = header[5], header[6]
    d = (artifact_dir / 'dictionary.bin').read_bytes()
    entries, pos = [], 0
    for _ in range(n_entries):
        entries.append(d[pos + 1:pos + 1 + d[pos]])
        pos += 1 + d[pos]
    assert pos == len(d)
    idx = (artifact_dir / 'index.bin').read_bytes()
    assert 0 <= i < n_records
    start = int.from_bytes(idx[2 * i:2 * i + 2], 'little')
    units = (artifact_dir / 'units.bin').read_bytes()
    body = units[start + 1:start + 1 + units[start]]
    return b''.join(entries[t - 0x80] if t >= 0x80 else bytes([t]) for t in body)


# ---- the golden numbers

def test_golden_breakdown_matches_hand_numbers() -> None:
    m = A.account(ARTIFACTS)
    for c in A.COMPONENTS + ('total',):
        assert m[c] == EXPECTED['bytes'][c], (c, m[c], EXPECTED['bytes'][c])
    assert m['opaque'] == 0
    assert m['records'] == EXPECTED['records']
    assert m['files'] == EXPECTED['files']
    assert sum(len(r) for r in TEST_RECORDS) == EXPECTED['raw_record_bytes']['total']


def test_golden_set_decodes_every_record_alone() -> None:
    """The counted files are enough: each record is returned from them alone, in random order."""
    order = list(range(len(TEST_RECORDS)))
    random.Random(7).shuffle(order)
    for i in order:
        assert _decode_gold1(ARTIFACTS, i) == TEST_RECORDS[i]


def test_full_report_passes() -> None:
    assert _problems(_full_report()) == []
    m = A.require(ARTIFACTS, _full_report(), test_records=TEST_RECORDS, train_records=TRAIN_RECORDS)
    assert m['total'] == 50


# ---- each left-out component fails

def test_omitting_dictionary_bytes_fails() -> None:
    p = _problems(_dropped('dictionary'))
    assert any('omits dictionary' in s for s in p), p
    assert any('reported total 40 != 50' in s for s in p), p
    _expect_error(A.require, ARTIFACTS, _dropped('dictionary'))


def test_omitting_framing_bytes_fails() -> None:
    p = _problems(_dropped('framing'))
    assert any('omits framing' in s for s in p), p
    assert any('reported total 47 != 50' in s for s in p), p
    _expect_error(A.require, ARTIFACTS, _dropped('framing'))


def test_omitting_index_bytes_fails() -> None:
    p = _problems(_dropped('index'))
    assert any('omits index' in s for s in p), p
    assert any('reported total 42 != 50' in s for s in p), p
    _expect_error(A.require, ARTIFACTS, _dropped('index'))


def test_zeroed_component_fails_like_an_omitted_one() -> None:
    rep = _full_report()
    rep['bytes']['dictionary'] = 0
    rep['bytes']['total'] -= 10
    p = _problems(rep)
    assert any('dictionary: reported 0, artifacts hold 10' in s for s in p), p


# ---- a producer total that disagrees with the artifacts fails

def test_reported_total_disagreeing_with_artifacts_fails() -> None:
    rep = _full_report()
    rep['bytes']['total'] = 49            # components still sum to 50
    p = _problems(rep)
    assert any('sum to 50, reported total is 49' in s for s in p), p
    assert any('reported total 49 != 50' in s for s in p), p


def test_self_consistent_but_short_report_fails() -> None:
    """Components and total agree with each other, but not with the files."""
    rep = _full_report()
    rep['bytes']['payload'] -= 4
    rep['bytes']['total'] -= 4
    p = _problems(rep)
    assert p == ['payload: reported 18, artifacts hold 22', 'reported total 46 != 50 bytes in the artifact files'], p


def test_record_count_disagreeing_fails() -> None:
    rep = _full_report()
    rep['records'] = 4
    assert any('reported 4 records' in s for s in _problems(rep))


# ---- the artifact set itself cannot hide bytes

def test_unlisted_file_in_artifact_set_fails() -> None:
    """A dictionary kept beside the set but left out of the manifest is caught."""
    with _copy_of_set() as d:
        (d / 'shared.dict').write_bytes(b'kept outside the count')
        assert 'shared.dict' in _expect_error(A.account, d)


def test_listed_file_missing_fails() -> None:
    with _copy_of_set() as d:
        (d / 'dictionary.bin').unlink()
        assert 'dictionary.bin' in _expect_error(A.account, d)


def test_index_that_does_not_match_units_fails() -> None:
    with _copy_of_set() as d:
        (d / 'index.bin').write_bytes(bytes.fromhex('0000 0700 0f00 1900'))
        assert 'unit boundaries' in _expect_error(A.account, d)


def test_units_that_do_not_walk_to_the_end_fail() -> None:
    with _copy_of_set() as d:
        (d / 'units.bin').write_bytes((ARTIFACTS / 'units.bin').read_bytes()[:-1])
        assert 'past the end' in _expect_error(A.account, d)


def test_opaque_archive_still_fails_on_a_dropped_component() -> None:
    """One blob: components cannot be checked one by one, but the total still can."""
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        blob = b''.join((ARTIFACTS / f).read_bytes() for f in ('header.bin', 'dictionary.bin', 'index.bin', 'units.bin'))
        (d / 'archive.bin').write_bytes(blob)
        (d / A.MANIFEST).write_text(json.dumps({'records': 3, 'files': [{'path': 'archive.bin', 'role': 'archive'}]}))
        assert _problems(_full_report(), d) == []
        for c in ('dictionary', 'framing', 'index'):
            assert any('!= 50' in s for s in _problems(_dropped(c), d)), c


def test_harness_shape_with_dictionary_folded_into_model() -> None:
    """A harness whose single `model` field holds the dictionary (header/model/index/framing/payload)."""
    rep = {'header': 7, 'model': 10, 'index': 8, 'framing': 3, 'payload': 22, 'total': 50}
    assert _problems(rep, model_includes_dictionary=True) == []
    short = {'header': 7, 'model': 0, 'index': 8, 'framing': 3, 'payload': 22, 'total': 40}
    assert any('model: reported 0, artifacts hold 10' in s for s in _problems(short, model_includes_dictionary=True))


# ---- leakage guard

def test_clean_dictionary_passes_leakage_guard() -> None:
    assert A.check_leakage(A.stored_model_bytes(ARTIFACTS), TEST_RECORDS, TRAIN_RECORDS) == []


def test_test_record_text_in_dictionary_fails() -> None:
    with _copy_of_set() as d:
        (d / 'dictionary.bin').write_bytes((d / 'dictionary.bin').read_bytes() + b'\x0alet x = 1;')
        p = A.check_leakage(A.stored_model_bytes(d), TEST_RECORDS, TRAIN_RECORDS)
        assert any("test record 2: 10 bytes at offset 0" in s for s in p), p
        msg = _expect_error(A.require, d, _full_report(), test_records=TEST_RECORDS, train_records=TRAIN_RECORDS)
        assert 'dictionary: reported 10, artifacts hold 21' in msg and 'test record 2' in msg


def test_test_only_byte_values_in_dictionary_fail() -> None:
    """The unseen-alphabet pattern: single-byte entries for bytes that occur only in test records."""
    with _copy_of_set() as d:
        (d / 'dictionary.bin').write_bytes((d / 'dictionary.bin').read_bytes() + b'\x01x\x01=\x011')
        p = A.check_leakage(A.stored_model_bytes(d), TEST_RECORDS, TRAIN_RECORDS)
        assert any('seen only in test records' in s and '1=x' in s for s in p), p


def test_full_byte_alphabet_is_not_a_leak() -> None:
    stored = A.stored_model_bytes(ARTIFACTS) + bytes(range(256))
    assert A.check_leakage(stored, TEST_RECORDS, TRAIN_RECORDS) == []


# ---- command line

def test_command_line_exit_status() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        good, bad = Path(tmp) / 'good.json', Path(tmp) / 'bad.json'
        good.write_text(json.dumps(_full_report()))
        bad.write_text(json.dumps(_dropped('index')))
        with contextlib.redirect_stdout(io.StringIO()):
            assert A.main([str(ARTIFACTS), '--report', str(good)]) == 0
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            assert A.main([str(ARTIFACTS), '--report', str(bad)]) == 1
        assert 'FAIL: report omits index bytes' in out.getvalue()


def _main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith('test_') and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f'PASS {name}')
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f'FAIL {name}: {type(exc).__name__}: {exc}')
    print(f'{len(tests) - failed}/{len(tests)} passed')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(_main())
