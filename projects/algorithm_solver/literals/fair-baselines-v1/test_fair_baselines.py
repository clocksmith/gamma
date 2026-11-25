#!/usr/bin/env python3
"""Unit tests for the fair-baselines harness.

    python3 -B test_fair_baselines.py            # plain run
    python3 -B -m pytest -p no:cacheprovider test_fair_baselines.py

Set FAIR_BASELINES_FSST_SRC to a checkout of github.com/cwida/fsst to include the reference FSST
baseline; without it that baseline must report `not-applicable`.
"""
from __future__ import annotations

import base64
import json
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fb_codecs as K  # noqa: E402
import fb_core as C  # noqa: E402
import fb_measure as M  # noqa: E402
import fb_native as N  # noqa: E402
from fb_candidate import load_candidate  # noqa: E402

NATIVE = N.load_native()

_WORDS_A = [b'@compute', b'@workgroup_size(64)', b'fn main(', b'vec3<f32>', b'let x = ', b'return', b';\n', b'{', b'}']
_WORDS_B = [b'"name":', b'"value":', b'true', b'false', b'null', b'[1,2,3]', b',', b'{', b'}', b'"id":']


def _records(n: int, seed: int) -> C.RecordSet:
    rng = random.Random(seed)

    def one(words):
        return b' '.join(rng.choice(words) for _ in range(rng.randrange(6, 40)))

    recs = [one(_WORDS_A) for _ in range(n)] + [one(_WORDS_B) for _ in range(n)]
    return C.RecordSet(recs, ['a'] * n + ['b'] * n, 'synthetic')


def _edge_records(seed: int) -> C.RecordSet:
    rs = _records(40, seed)
    rng = random.Random(seed + 1)
    rs.records[3] = b''                                              # empty record
    rs.records[5] = bytes(range(256))                                # every byte value, including 0x00 and 0xFF
    rs.records[7] = bytes(rng.randrange(256) for _ in range(700))    # incompressible, longer than 255 bytes
    rs.records[45] = b'\xff' * 300
    return rs


TRAIN, TEST = _records(60, 11), _edge_records(12)
OPTS = M.Options(grid='quick', lookups=2_000, rounds=1, timing=False)
_DOC = None


def _doc() -> dict:
    global _DOC
    if _DOC is None:
        _DOC = M.run(NATIVE, TRAIN, TEST, OPTS)
    return _DOC


def test_every_method_round_trips_or_says_why() -> None:
    for m in _doc()['methods']:
        if m['name'].startswith('fsst-reference') and not NATIVE.has_fsst:
            assert m['status'] == 'not-applicable', m
            continue
        assert m['status'] == 'ok', (m['name'], m.get('reason'), m.get('verification'))
        for tag in ('index4', 'compact_index'):
            assert m['verification'][tag]['ok'] and m['verification'][tag]['records_checked'] == len(TEST)


def test_accounting_sums_to_archive_length() -> None:
    ctx = K.TuneContext(NATIVE, TRAIN.records, grid='quick', groups=TRAIN.groups)
    for name, factory in K.build_baselines(NATIVE):
        try:
            codec = factory()
            codec.train(TRAIN.records, ctx)
            enc = codec.encode(TEST.records, TEST.groups)
        except K.NotApplicable:
            continue
        for width in (4, None):
            archive, acct = enc.pack(width)
            assert acct.total == len(archive), name
            assert acct.header + acct.model + acct.index + acct.framing + acct.payload == len(archive), name
        archive4, acct4 = enc.pack(4)
        archivec, acctc = enc.pack(None)
        assert len(archivec) <= len(archive4), name
        assert acct4.payload == acctc.payload and acct4.model == acctc.model and acct4.framing == acctc.framing, name
        if enc.parts is None and 'lane_form_bytes_exact' not in enc.detail:
            # lane form: 10-byte header instead of 16, same model, same 4-byte index, same stored bytes
            assert enc.lane_form_bytes() == len(archive4) - (C.HEADER_BYTES - C.LANE_HEADER_BYTES), name


def test_zstd_framing_is_measured() -> None:
    recs = [b'abcdefgh' * 12, b'fn main() { return vec3<f32>(1.0); }' * 3, b'x' * 300]
    d = NATIVE.zdict_train(N.ZDICT_FASTCOVER, K.zstd_cli_sample_order(TRAIN.records), 1024, 3)
    for framing, per_small, per_big in (('frame', 13, 14), ('lean-frame', 5, 5)):
        enc = K._zstd_units(NATIVE, recs, dict_bytes=d, dict_is_raw=False, level=19, framing=framing)
        # standard: 4 magic + 1 descriptor + 4 dictionary ID + 1 or 2 content size + 3 block header
        # lean:     1 descriptor + 1 window + 3 block header
        assert enc.unit_framing == [per_small, per_small, per_big], (framing, enc.unit_framing)
    blk = K._zstd_units(NATIVE, recs, dict_bytes=d, dict_is_raw=False, level=19, framing='raw-block')
    assert blk.unit_framing == [0, 0, 0] and len(blk.aux) == 1
    _, acct = blk.pack(4)
    assert acct.framing == 1   # only the stored-raw flag bitmap
    lean = K._zstd_units(NATIVE, recs, dict_bytes=d, dict_is_raw=False, level=19, framing='lean-frame')
    # the raw block is the frame's block content with the 5 framing bytes gone
    assert [len(u) for u in blk.units] == [len(u) - 5 for u in lean.units]


def test_verification_catches_a_changed_byte() -> None:
    enc = K.RawCodec().encode(TEST.records)
    archive, _ = enc.pack(4)
    bad = bytearray(archive)
    bad[-1] ^= 0x01
    rd = NATIVE.open(bytes(bad))
    res = M.verify(rd, TEST.records, 1, 2048)
    rd.close()
    assert not res['ok'] and res['problem'] == 'bytes differ'
    truncated = archive[:-3]
    try:
        NATIVE.open(truncated)
    except N.NativeError:
        pass
    else:
        raise AssertionError('a truncated archive must not open')


def test_model_does_not_depend_on_the_test_records() -> None:
    models = []
    for test in (TEST, _records(30, 99)):
        ctx = K.TuneContext(NATIVE, TRAIN.records, grid='quick', groups=TRAIN.groups)
        codec = K.ZstdTunedCodec(NATIVE, 'raw-block')
        codec.train(TRAIN.records, ctx)
        enc = codec.encode(test.records)
        models.append((codec.cfg, enc.model))
    assert models[0] == models[1]


def test_block_method_reports_bytes_decoded_per_lookup() -> None:
    by = {m['name']: m for m in _doc()['methods']}
    one = by['zstd-lean-frame-tuned']['per_lookup']['mean_raw_bytes_decoded']
    four = by['zstd-lean-frame-blocks-of-4']['per_lookup']['mean_raw_bytes_decoded']
    assert abs(one - TEST.total_bytes / len(TEST)) < 0.01
    assert four > 2 * one


def test_record_loading_from_directory_and_jsonl() -> None:
    with tempfile.TemporaryDirectory(prefix='fb-test-') as tmp:
        d = Path(tmp) / 'recs'
        (d / 'g1').mkdir(parents=True)
        (d / 'g2').mkdir()
        (d / 'g1' / '0001.bin').write_bytes(b'\x00\xffone')
        (d / 'g1' / '0000.bin').write_bytes(b'zero')
        (d / 'g2' / '0000.bin').write_bytes(b'two')
        rs = C.load_records(d)
        assert rs.records == [b'zero', b'\x00\xffone', b'two'] and rs.groups == ['g1', 'g1', 'g2']
        j = Path(tmp) / 'recs.jsonl'
        j.write_text('\n'.join([
            json.dumps('plain string'),
            json.dumps({'text': 'h' + chr(0xE9) + 'llo', 'group': 'x'}),
            json.dumps({'base64': base64.b64encode(b'\x00\x01\xff').decode(), 'group': 'y'}),
        ]) + '\n', encoding='utf-8')
        rs = C.load_records(j)
        assert rs.records == [b'plain string', ('h' + chr(0xE9) + 'llo').encode('utf-8'), b'\x00\x01\xff']
        assert rs.groups == ['', 'x', 'y']


def test_candidate_plugin_is_measured_in_the_same_loop() -> None:
    cand = load_candidate(str(HERE / 'examples' / 'candidate_example.py') + ':XorCandidate')
    opts = M.Options(grid='quick', lookups=2_000, rounds=1, methods=('raw-indexed',))
    doc = M.run(NATIVE, TRAIN, TEST, opts, candidates=[cand])
    by = {m['name']: m for m in doc['methods']}
    c = by['example-xor']
    assert c['status'] == 'ok', c
    assert c['bytes']['all_in']['total'] == 8 + 4 * len(TEST) + TEST.total_bytes
    assert by['raw-indexed']['lookup_timing']['kind'] == 'native-loop'
    if shutil.which('cc'):
        assert c['verification']['native_decoder']['ok']
        assert c['lookup_timing']['kind'] == 'native-loop'
    else:
        assert c['lookup_timing']['comparable_with_native'] is False


def test_candidate_with_wrong_accounting_is_rejected() -> None:
    cand = load_candidate(str(HERE / 'examples' / 'candidate_example.py') + ':XorCandidate')
    real_encode = cand.cand.encode

    def bad_encode(records, groups):
        res = real_encode(records, groups)
        res['accounting']['payload'] -= 1
        return res

    cand.cand.encode = bad_encode
    doc = M.run(NATIVE, TRAIN, TEST, M.Options(grid='quick', timing=False, methods=('raw-indexed',)), candidates=[cand])
    assert {m['name']: m['status'] for m in doc['methods']}['example-xor'] == 'error'


def test_dictionaries_match_the_zstd_cli() -> None:
    zstd = shutil.which('zstd')
    if not zstd:
        print('  (skipped: zstd CLI not installed)')
        return
    version = subprocess.run([zstd, '--version'], capture_output=True, text=True).stdout
    if NATIVE.zstd_version not in version:
        print('  (skipped: zstd CLI and library versions differ)')
        return
    with tempfile.TemporaryDirectory(prefix='fb-test-') as tmp:
        paths = []
        for i, r in enumerate(TRAIN.records):
            p = Path(tmp) / f's_{i:04d}.bin'
            p.write_bytes(r)
            paths.append(str(p))
        out = Path(tmp) / 'dict.bin'
        subprocess.run([zstd, '--train', '--maxdict=1024', '-q', *paths, '-o', str(out)], check=True,
                       capture_output=True)
        ctx = K.TuneContext(NATIVE, TRAIN.records, grid='quick')
        assert ctx.zdict('all', TRAIN.records, 'fastcover', 1024, K.LANE_DICT_TRAIN_LEVEL) == out.read_bytes()
        src = Path(tmp) / 'rec.bin'
        src.write_bytes(TEST.records[0])
        subprocess.run([zstd, '-19', '--no-check', '-q', '-f', '-D', str(out), str(src)], check=True, capture_output=True)
        mine = NATIVE.zstd_encode_many([TEST.records[0]], dict_bytes=out.read_bytes(), dict_is_raw=False, level=19,
                                       mode=N.ZSTD_MODE_FRAME)[0]
        assert mine == Path(str(src) + '.zst').read_bytes()


def _main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith('test_') and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f'ok    {name}')
        except Exception as exc:   # report every failure, then exit non-zero
            failed += 1
            print(f'FAIL  {name}: {type(exc).__name__}: {exc}')
    print(f'{len(tests) - failed} passed, {failed} failed'
          + ('' if NATIVE.has_fsst else ' (reference FSST not built: FAIR_BASELINES_FSST_SRC not set)'))
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(_main())
