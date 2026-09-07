"""Independent raw-reversal framing, inverse, and bounded synthetic CLI checks."""
import bz2
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import signal
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from programs.baseline_bz2 import program as baseline
from tools import raw_reverse_bz2_v1 as codec

HEADER, FRAME = struct.Struct('<8sIIQ'), struct.Struct('<IIB32s')
MAGIC = b'D2REVB01'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def common(report):
    return {key: value for key, value in report.items() if key != 'requested_mode'}


def fixtures():
    rng = random.Random(871)
    pieces = []
    while sum(map(len, pieces)) < 8192:
        stem = bytes(rng.choice(b'abcdefghijklmnopqrstuvwxyz') for _ in range(11))
        pieces.append(b'prefix:' + stem + b':repeated-suffix\n')
    return {'asymmetric8192': b''.join(pieces)[:8192],
            'random2048': random.Random(491).randbytes(2048)}


def unpack(archive):
    magic, block_size, count, total = HEADER.unpack_from(archive)
    cursor, rows = HEADER.size, []
    for _ in range(count):
        raw_size, size, direction, digest = FRAME.unpack_from(archive, cursor)
        cursor += FRAME.size
        payload = archive[cursor:cursor + size]
        cursor += size
        rows.append((raw_size, direction, digest, payload))
    if cursor != len(archive):
        raise AssertionError('independent framing parser did not consume archive')
    return (magic, block_size, count, total), rows


def framed(raw, payload, direction=0, raw_size=None, digest=None):
    size = len(raw) if raw_size is None else raw_size
    return (HEADER.pack(MAGIC, max(1, size), 1, size)
            + FRAME.pack(size, len(payload), direction, hashlib.sha256(raw).digest() if digest is None else digest)
            + payload)


class RawReverseIndependentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = Path(tempfile.mkdtemp(prefix='raw_reverse_independent_'))
        for name, raw in fixtures().items():
            (cls.evidence / (name + '.raw')).write_bytes(raw)

    def retain(self, name, value):
        (self.evidence / name).write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')

    def check_archive(self, raw, mode, block_size):
        archive, report = codec.encode(raw, mode, block_size)
        restored, decoded = codec.decode(archive)
        repeated, again = codec.encode(restored, mode, block_size)
        self.assertEqual(restored, raw)
        self.assertEqual(repeated, archive)
        self.assertEqual(again, report)
        self.assertEqual(common(report), decoded)
        header, blocks = unpack(archive)
        self.assertEqual(header, (MAGIC, block_size, (len(raw) + block_size - 1) // block_size, len(raw)))
        self.assertEqual(report['archive_sha256'], sha(archive))
        self.assertEqual(report['raw_sha256'], sha(raw))
        self.assertEqual(sum(report['costs'].values()), len(archive))
        self.assertEqual(report['costs']['framing'], 24 + 41 * len(blocks))
        self.assertEqual(report['complete_archive_bytes'], len(archive))
        self.assertEqual(len(report['frames']), len(blocks))
        for i, (raw_size, direction, digest, payload) in enumerate(blocks):
            part = raw[i * block_size:(i + 1) * block_size]
            coded = part[::-1] if mode == 'D' else part
            self.assertEqual(raw_size, len(part))
            self.assertEqual(direction, int(mode == 'D'))
            self.assertEqual(digest, hashlib.sha256(part).digest())
            self.assertEqual(payload, baseline.compress(coded))
            self.assertEqual(baseline.decompress(payload), coded)
            row = report['frames'][i]
            self.assertEqual(row['coded_bytes_sha256'], sha(coded))
            self.assertEqual(row['raw_sha256'], sha(part))
            self.assertEqual(row['output_sha256'], sha(part))
            self.assertEqual(row['complete_frame_bytes'], FRAME.size + len(payload))
            self.assertEqual(sum(row['costs'].values()), FRAME.size + len(payload))
        return archive, report

    def test_empty_nonpalindrome_allbytes_and_partial_blocks(self):
        cases = [b'', b'\0', b'ab', b'\0\xff\x01abc\0', bytes(range(256)),
                 bytes(range(256)) * 3 + b'partial', b'x' * 257]
        for raw in cases:
            for block_size in (1, 257, 250000):
                rows = {}
                for mode in ('P', 'K', 'D'):
                    with self.subTest(raw_bytes=len(raw), block_size=block_size, mode=mode):
                        rows[mode] = self.check_archive(raw, mode, block_size)[0]
                self.assertEqual(rows['P'], rows['K'])
                if not raw:
                    self.assertEqual(rows['P'], HEADER.pack(MAGIC, block_size, 0, 0))
                    self.assertEqual(rows['D'], rows['P'])

    def test_reversal_is_inside_each_block_and_is_forced(self):
        raw = b'abcdXYZ'
        archive, _ = self.check_archive(raw, 'D', 4)
        _, rows = unpack(archive)
        self.assertEqual([bz2.decompress(row[3]) for row in rows], [b'dcba', b'ZYX'])
        # Even a palindrome retains a reverse direction marker; no size fallback.
        parent, _ = codec.encode(b'aba', 'P')
        treatment, _ = codec.encode(b'aba', 'D')
        self.assertEqual(unpack(parent)[1][0][3], unpack(treatment)[1][0][3])
        self.assertEqual(unpack(treatment)[1][0][1], 1)
        self.assertNotEqual(parent, treatment)

    def test_truncation_at_every_byte_and_archive_trailing(self):
        good, _ = codec.encode(b'\0aab\xffsuffix', 'D', 7)
        for end in range(len(good)):
            with self.subTest(end=end), self.assertRaises(ValueError):
                codec.decode(good[:end])
        for suffix in (b'\0', b'trailing', good):
            with self.assertRaises(ValueError):
                codec.decode(good + suffix)

    def test_bzip2_single_stream_termination_and_expansion_bound(self):
        raw = b'abc'
        payload = bz2.compress(raw, 9)
        invalid = [payload[:-1], payload + b'x', payload + bz2.compress(b'', 9),
                   payload + bz2.compress(b'abc', 9), b'not-bzip2',
                   bz2.compress(b'ab', 9), bz2.compress(b'abcd', 9),
                   bz2.compress(b'x' * 8192, 9)]
        for packed in invalid:
            with self.subTest(payload_sha256=sha(packed)), self.assertRaises(ValueError):
                codec.decode(framed(raw, packed))

    def test_header_frame_direction_digest_and_output_limits(self):
        raw = b'nonpalindrome'
        good, _ = codec.encode(raw, 'P')
        self.assertEqual(codec.decode(good, max_output=len(raw))[0], raw)
        for limit in (-1, 0, len(raw) - 1, True, 1.5):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                codec.decode(good, max_output=limit)
        fields = list(HEADER.unpack_from(good))
        for index, value in ((0, b'wrongMAG'), (1, 0), (1, 250001), (2, 0), (2, 2), (3, 1000001)):
            changed = fields.copy(); changed[index] = value
            with self.subTest(header=index, value=value), self.assertRaises(ValueError):
                codec.decode(HEADER.pack(*changed) + good[HEADER.size:])
        raw_size, size, direction, digest = FRAME.unpack_from(good, HEADER.size)
        for frame in ((raw_size - 1, size, direction, digest), (raw_size, 0, direction, digest),
                      (raw_size, size, 2, digest), (raw_size, size, 1, digest),
                      (raw_size, size, direction, b'\0' * 32)):
            corrupt = good[:HEADER.size] + FRAME.pack(*frame) + good[HEADER.size + FRAME.size:]
            with self.subTest(frame=frame[:3]), self.assertRaises(ValueError):
                codec.decode(corrupt)

    def test_archive_cap_boundary_and_early_header_bound(self):
        for mode in ('P', 'K', 'D'):
            expected, _ = codec.encode(b'x', mode, 1)
            with patch.object(codec, 'MAX_ARCHIVE', len(expected) - 1):
                with self.assertRaises(ValueError):
                    codec.encode(b'x', mode, 1)
                with self.assertRaises(ValueError):
                    codec.decode(expected)
            with patch.object(codec, 'MAX_ARCHIVE', len(expected)):
                self.assertEqual(codec.encode(b'x', mode, 1)[0], expected)
                self.assertEqual(codec.decode(expected)[0], b'x')
        with patch.object(codec, 'MAX_ARCHIVE', HEADER.size + 2 * FRAME.size - 1), \
                patch.object(codec.bz2, 'compress', side_effect=AssertionError('compression reached')):
            with self.assertRaisesRegex(ValueError, 'framing'):
                codec.encode(b'xy', 'D', 1)
        with patch.object(codec, 'MAX_ARCHIVE', HEADER.size - 1):
            with self.assertRaises(ValueError):
                codec.encode(b'')
        self.retain('archive-cap.json', dict(one_byte_complete_bytes=len(expected),
            rejection_cap=len(expected) - 1, acceptance_cap=len(expected),
            all_modes=True, framing_lower_bound_rejects_before_compression=True))

    def test_encoder_input_limits(self):
        for raw, mode, size in ((bytearray(b'a'), 'P', 1), (b'a', 'X', 1),
                                (b'a', 'P', 0), (b'a', 'P', 250001), (b'a', 'P', True)):
            with self.subTest(mode=mode, block_size=size), self.assertRaises(ValueError):
                codec.encode(raw, mode, size)
        with patch.object(codec, 'MAX_RAW', 8):
            with self.assertRaises(ValueError):
                codec.encode(b'x' * 9)

    def test_new_file_preserves_existing_and_removes_failed_write(self):
        path = self.evidence / 'existing.bin'
        path.write_bytes(b'original')
        with self.assertRaises(FileExistsError):
            codec.new_file(path, b'replacement')
        self.assertEqual(path.read_bytes(), b'original')
        failed = self.evidence / 'failed-write.bin'
        with patch.object(codec.os, 'fsync', side_effect=OSError('synthetic fsync failure')):
            with self.assertRaises(OSError):
                codec.new_file(failed, b'incomplete')
        self.assertFalse(failed.exists())

    def phase(self, name, argv, expected_rc=0):
        stdout, stderr = self.evidence / (name + '.stdout.json'), self.evidence / (name + '.stderr.log')
        command = [sys.executable, str(ROOT / 'tools/raw_reverse_bz2_v1.py'), *map(str, argv)]
        bound_paths = [ROOT / 'tools/raw_reverse_bz2_v1.py', Path(__file__),
                       ROOT / 'programs/baseline_bz2/program.py',
                       ROOT / 'operations/provenance/raw_reverse_bz2_v1_plan.json', Path(argv[1])]
        before = [dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path.read_bytes()))
                  for path in bound_paths]
        self.retain(name + '.invocation.json', dict(argv=command, input_and_source_bindings=before))
        started = time.monotonic()
        with stdout.open('xb') as out, stderr.open('xb') as err:
            child = subprocess.Popen(command, cwd=ROOT, stdout=out, stderr=err)
            while True:
                pid, status, usage = os.wait4(child.pid, os.WNOHANG)
                if pid:
                    break
                if time.monotonic() - started > 80:
                    child.kill()
                    pid, status, usage = os.wait4(child.pid, 0)
                    break
                time.sleep(.01)
            child.returncode = os.waitstatus_to_exitcode(status)
        after = [dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path.read_bytes()))
                 for path in bound_paths]
        receipt = dict(argv=command, returncode=child.returncode, elapsed_seconds=time.monotonic() - started,
            user_cpu_seconds=usage.ru_utime, system_cpu_seconds=usage.ru_stime,
            peak_process_rss_kib=usage.ru_maxrss, affinity=sorted(os.sched_getaffinity(0)),
            address_space_limit=resource.getrlimit(resource.RLIMIT_AS),
            cpu_limit=resource.getrlimit(resource.RLIMIT_CPU),
            file_size_limit=resource.getrlimit(resource.RLIMIT_FSIZE),
            timing_authority='shared-host diagnostic', corpus_bytes_opened=0,
            input_and_source_bindings=before, sources_and_input_unchanged=before == after)
        self.retain(name + '.execution.json', receipt)
        self.assertEqual(before, after)
        if expected_rc == 0:
            self.assertEqual(child.returncode, 0, stderr.read_text())
            return json.loads(stdout.read_text()), receipt
        self.assertNotEqual(child.returncode, 0)
        return None, receipt

    def test_fixed_synthetic_cli_exact_raw_repeats_and_kernel_resources(self):
        summaries = {}
        for name, raw in fixtures().items():
            source = self.evidence / (name + '.raw')
            arms = {}
            for mode in ('P', 'K', 'D'):
                stem = name + '.' + mode
                archive, inverse, repeated = [self.evidence / (stem + suffix)
                                             for suffix in ('.d2r', '.inverse', '.repeat.d2r')]
                enc, enc_exec = self.phase(stem + '.encode', ['encode', source, archive, '--mode', mode])
                dec, dec_exec = self.phase(stem + '.decode', ['decode', archive, inverse])
                rep, rep_exec = self.phase(stem + '.repeat', ['encode', inverse, repeated, '--mode', mode])
                self.assertEqual(inverse.read_bytes(), raw)
                self.assertEqual(archive.read_bytes(), repeated.read_bytes())
                self.assertEqual(enc['result'], rep['result'])
                self.assertEqual(common(enc['result']), dec['result'])
                expected, _ = self.check_archive(raw, mode, 250000)
                self.assertEqual(archive.read_bytes(), expected)
                arms[mode] = dict(archive_bytes=len(expected), archive_sha256=sha(expected),
                    report=enc['result'], phase_resources={'encode': enc_exec, 'decode': dec_exec, 'repeat': rep_exec},
                    codec_resources={key: {field: value[field] for field in
                        ('cpu_seconds', 'elapsed_seconds', 'peak_process_rss_kib')}
                        for key, value in [('encode', enc), ('decode', dec), ('repeat', rep)]})
            self.assertEqual(arms['P']['archive_sha256'], arms['K']['archive_sha256'])
            summaries[name] = dict(raw_bytes=len(raw), raw_sha256=sha(raw), arms=arms,
                direction_delta_bytes=arms['D']['archive_bytes'] - arms['P']['archive_bytes'])
        existing = self.evidence / 'asymmetric8192.P.d2r'
        before = existing.read_bytes()
        self.phase('existing-output-refused', ['encode', self.evidence / 'random2048.raw', existing], expected_rc=1)
        self.assertEqual(existing.read_bytes(), before)
        self.retain('kernel.json', dict(fixtures=summaries, actual_cli_phases=18,
            additional_negative_cli_phases=1, complete_package_bytes=None, full_corpus_score_bytes=None,
            exact_inverse=True, deterministic_raw_repeats=True, encoder_decoder_common_reports_equal=True,
            recipe='8192 bytes: Random871 lowercase11-byte stems between prefix: and :repeated-suffix\\n; truncate joined records. 2048 bytes: Random491.randbytes(2048).'))


if __name__ == '__main__':
    unittest.main()
