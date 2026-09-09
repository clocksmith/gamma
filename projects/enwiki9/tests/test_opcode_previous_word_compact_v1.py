"""Synthetic semantic parity of compact packaging and the published word adapter."""
import hashlib
import json
import lzma
import os
from pathlib import Path
import re
import struct
import sys
import tempfile
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import opcode_previous_word_build_v1 as original
from tools import opcode_previous_word_compact_build_v1 as compact
from tools import opcode_previous_word_observe_v1 as observe
from tools import opcode_previous_word_compact_observe_v1 as compact_observe

FIXTURES = {
    'empty': b'',
    'no_letters': b'1234\t'*16,
    'arbitrary': bytes(range(256))+b'<broken\x00\xff',
    'boundaries': b'First second abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ \tX  Y\n',
    'overlap': b'alpha beta gamma delta\n'*12+b'alpha beta delta gamma\n'*8,
    'opcodes': b'<title>Oak\x00</title><text xml:space="preserve">Elm Birch Elm Birch</text>\r\n'*4,
}


class CompactWordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if len(FIXTURES) > 6 or sum(map(len, FIXTURES.values())) > 4096:
            raise ValueError('synthetic fixture budget exceeded')
        retained = os.environ.get('GAMMA_PREVIOUS_WORD_COMPACT_UNIT_RESULTS')
        if retained:
            cls.directory = Path(retained)
            cls.directory.mkdir(parents=True, exist_ok=False)
        else:
            tmp = tempfile.TemporaryDirectory(dir=ROOT / 'results', prefix='previous_word_compact_unit_')
            cls.addClassCleanup(tmp.cleanup); cls.directory = Path(tmp.name)
        cls.modules = {}
        for name, builder in (('original', original), ('compact', compact)):
            output = cls.directory / name; builder.write_bundle(output)
            cls.modules[name] = observe.load(output / 'program.py')

    def test_all_arms_exact_observed_plain_decode_repeat_parity(self):
        for name, raw in FIXTURES.items():
            kept = self.directory / name; kept.mkdir()
            (kept / 'input.raw').write_bytes(raw)
            rows = {}
            for arm in 'PKDS':
                versions = {}
                for version, module in self.modules.items():
                    with self.subTest(fixture=name, arm=arm, version=version):
                        execute = compact_observe.execute if version == 'compact' else observe.execute
                        archive, audit = execute(module, 'encode', raw, arm)
                        restored, decoded = execute(module, 'decode', archive, arm)
                        repeat, repeated = execute(module, 'encode', restored, arm)
                        plain, none = execute(module, 'encode', raw, arm, False)
                        plain_raw, none_decode = execute(module, 'decode', archive, arm, False)
                        self.assertEqual(restored, raw); self.assertEqual(plain_raw, raw)
                        self.assertEqual(archive, repeat); self.assertEqual(archive, plain)
                        self.assertIsNone(none); self.assertIsNone(none_decode)
                        observe.compare_audits(audit, decoded); observe.compare_audits(audit, repeated)
                        self.assertEqual(sum(audit['updates_by_mode']), audit['parent']['predictor_bits'])
                        self.assertEqual(audit['parent']['predictor_bits'], 8*audit['parent']['modeled_bytes'])
                        versions[version] = archive, audit
                        for suffix, value in (('arc', archive), ('raw', restored), ('repeat.arc', repeat), ('plain.arc', plain)):
                            (kept / f'{version}-{arm}.{suffix}').write_bytes(value)
                        for suffix, value in (('encode', audit), ('decode', decoded), ('repeat', repeated)):
                            (kept / f'{version}-{arm}-{suffix}.audit.json').write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')
                self.assertEqual(versions['original'][0], versions['compact'][0])
                observe.compare_audits(versions['original'][1], versions['compact'][1])
                rows[arm] = versions['compact']
            self.assertEqual(rows['P'][0], rows['K'][0])
            self.assertEqual(rows['P'][1]['parent'], rows['K'][1]['parent'])
            for arm in 'KDS':
                for field in ('parse_sha256', 'parse_events', 'updates_by_mode'):
                    self.assertEqual(rows['P'][1][field], rows[arm][1][field])
                self.assertEqual(rows['K'][1]['word_history_sha256'], rows[arm][1]['word_history_sha256'])
            if name in ('boundaries', 'overlap', 'opcodes'):
                modeled = self.modules['compact'].namespace('P')['oe'](raw)
                words = re.findall(rb'[A-Za-z]+(?=[^A-Za-z])', modeled)
                expected = [w[-8:].hex() for w in words[-2:][::-1]]
                self.assertEqual(rows['D'][1]['completed_words_hex'], expected)
                self.assertNotEqual(rows['D'][1]['word_history_sha256'], rows['P'][1]['word_history_sha256'])
            if name == 'overlap': self.assertGreater(sum(rows['D'][1]['updates_by_mode'][1:]), 0)
            if name in ('empty', 'no_letters'): self.assertEqual(rows['D'], rows['S'])
            print(json.dumps(dict(fixture=name, raw_bytes=len(raw), exact_all_arm_parity=True,
                archives={a:dict(bytes=len(v[0]),sha256=hashlib.sha256(v[0]).hexdigest()) for a,v in rows.items()})))

    def test_original_prefix_costs_all_modes(self):
        for name, raw in FIXTURES.items():
            costs = {}
            for version, module in self.modules.items():
                for arm in 'PKDS':
                    ns = module.namespace(arm); modeled = ns['oe'](raw); ns['_limit'] = len(modeled)
                    costs[version, arm] = ns['lit_prefix'](modeled)
            for key, value in costs.items():
                with self.subTest(fixture=name, mode=key):
                    self.assertEqual(value, costs['original', 'P'])

    def test_fresh_namespaces_isolate_arm_modes_and_model_state(self):
        module = self.modules['compact']; raw = FIXTURES['boundaries']
        saved = {}
        for arm in 'PKDS':
            ns = module.namespace(arm); modeled = ns['oe'](raw); ns['_limit'] = len(modeled)
            state, literal = ns['GST'](), ns['LIT']()
            for byte in modeled: state.up(byte)
            saved[arm] = ns, state, literal, literal.keys(state, 5), observe.history(state)
        self.assertNotEqual(saved['D'][3][11], saved['S'][3][11])
        self.assertEqual(saved['P'][3], saved['K'][3])
        for arm in 'SDKPS':
            fresh = module.namespace(arm)
            self.assertTrue(all(fresh is not previous[0] for previous in saved.values()))
            self.assertEqual(observe.history(fresh['GST']())[1], (b'', b''))
            self.assertTrue(all(not table for table in fresh['LIT']().tt))
            fresh['compress'](raw)
            for old_arm, (_, state, literal, keys, history) in saved.items():
                with self.subTest(new_arm=arm, old_arm=old_arm):
                    self.assertEqual(literal.keys(state, 5), keys)
                    self.assertEqual(observe.history(state), history)
                    self.assertTrue(all(not table for table in literal.tt))

    def test_malformed_and_truncated_archives_rejected(self):
        raw = FIXTURES['boundaries']
        for arm in 'PKDS':
            archive, _ = compact_observe.execute(self.modules['compact'], 'encode', raw, arm, False)
            malformed = (b'', archive[:1], archive[:8], archive[:-1], archive+b'x',
                         struct.pack('>II', 0, 1)+b'\x80')
            for version, module in self.modules.items():
                for index, value in enumerate(malformed):
                    with self.subTest(arm=arm, version=version, mutation=index), self.assertRaises(ValueError):
                        execute = compact_observe.execute if version == 'compact' else observe.execute
                        execute(module, 'decode', value, arm, False)

    def test_tracking_sentinel_rejected_on_byte_and_empty_terminal(self):
        module = self.modules['compact']
        for arm in 'PKDS':
            def broken_namespace(selected):
                ns = module.namespace(selected); base = ns['GST']
                class Broken(base):
                    def __init__(self, words=True):
                        super().__init__(words)
                        if words:
                            self._completed_words = (b'', b'') if selected == 'P' else None
                ns['GST'] = Broken
                return ns
            broken = types.SimpleNamespace(namespace=broken_namespace)
            for name in ('empty', 'no_letters'):
                with self.subTest(arm=arm, fixture=name), self.assertRaisesRegex(ValueError, 'tracking state differs'):
                    compact_observe.execute(broken, 'encode', FIXTURES[name], arm)

    def test_deterministic_bundle_and_authenticated_source(self):
        files = compact.bundle(); self.assertEqual(set(files), {'p', 'program.py'})
        self.assertEqual(files, compact.bundle())
        source = compact.source()
        self.assertEqual(source, compact.source())
        self.assertEqual(lzma.decompress(files['p']), source.encode() if isinstance(source, str) else source)
        relocated = self.directory / 'relocated'; compact.write_bundle(relocated)
        for name, data in files.items(): self.assertEqual((relocated / name).read_bytes(), data)
        with self.assertRaises(FileExistsError): compact.write_bundle(relocated)
        mismatch = self.directory / 'mismatch'; parent = mismatch / compact.PARENT
        parent.parent.mkdir(parents=True); parent.write_bytes(b'wrong parent')
        with self.assertRaises(ValueError): compact.source(mismatch)
        with self.assertRaises(ValueError): compact.bundle(mismatch)


if __name__ == '__main__':
    unittest.main()
