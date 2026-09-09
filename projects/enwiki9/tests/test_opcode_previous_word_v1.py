"""Synthetic checks; no corpus or candidate directory access beyond parent p."""
import hashlib
import lzma
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from lib.opcode_previous_word_v1 import install, PARENT_SHA
from opcode_previous_word_build_v1 import bundle, write_bundle, PARENT, MUTATION


def namespace(arm):
    packed = (ROOT / PARENT).read_bytes()
    ns = {'__name__': 'previous_word_synthetic'}
    exec(compile(lzma.decompress(packed), '<parent>', 'exec'), ns)
    return install(ns, packed, arm)


class PreviousWordTests(unittest.TestCase):
    def test_bindings_and_unchanged_parent(self):
        packed = (ROOT / PARENT).read_bytes()
        self.assertEqual(hashlib.sha256(packed).hexdigest(), PARENT_SHA)
        ns = namespace('P'); before = ns.copy()
        self.assertIs(install(ns, packed, 'P'), ns)
        self.assertEqual(ns, before)
        self.assertFalse(hasattr(ns['GST'](), 'completed_words'))
        for arm in ('P', 'K', 'D', 'S'):
            with self.assertRaises(ValueError): install({}, packed + b'x', arm)
        with self.assertRaises(ValueError): install({}, packed, 'unknown')

    def test_history_boundaries_and_long_words(self):
        for arm in ('K', 'D', 'S'):
            ns = namespace(arm); ns['_limit'] = 4096; st = ns['GST']()
            self.assertEqual(st.completed_words(), (b'', b''))
            for byte in b'  First': st.up(byte)
            self.assertEqual(st.completed_words(), (b'', b''))
            st.up(32)
            self.assertEqual(st.completed_words(), (b'First', b''))
            for byte in b'!\t abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ': st.up(byte)
            self.assertEqual(st.completed_words(), (b'First', b''))
            st.up(10)
            self.assertEqual(st.completed_words(), (b'STUVWXYZ', b'First'))
            for byte in b'\xff7_\r': st.up(byte)
            self.assertEqual(st.completed_words(), (b'STUVWXYZ', b'First'))
            for byte in b'x ': st.up(byte)
            self.assertEqual(st.completed_words(), (b'x', b'STUVWXYZ'))

    def test_keys_and_parent_state_projection(self):
        models = {a: namespace(a) for a in ('P', 'K', 'D', 'S')}
        states = {}; literals = {}
        for arm, ns in models.items():
            ns['_limit'] = 4096; states[arm] = ns['GST'](); literals[arm] = ns['LIT']()
            self.assertEqual(len(literals[arm].tt), 12)
        for byte in b'Oak Elm ab!\n\x00\xffBirch ':
            original = literals['P'].keys(states['P'], 5)
            self.assertEqual(literals['K'].keys(states['K'], 5), original)
            for arm in ('D', 'S'):
                st = states[arm]; keys = literals[arm].keys(st, 5)
                self.assertEqual(len(keys), 12)
                self.assertEqual(keys[:11], original[:11])
                self.assertEqual(keys[11], (5, st.completed_words()[arm == 'S'], bytes(st.word[-2:]), st.f))
            for st in states.values(): st.up(byte)
            for arm in ('K', 'D', 'S'):
                for name, value in vars(states['P']).items():
                    actual = getattr(states[arm], name)
                    self.assertEqual(vars(actual) if name == 'field' else actual,
                                     vars(value) if name == 'field' else value)

    def test_opcodes_escapes_and_original_prefix(self):
        raw = b'<title>Oak</title><text xml:space="preserve">Elm\x00Birch</text>'
        self.assertLessEqual(len(raw), 4096)
        prefixes = {}; histories = {}
        for arm in ('P', 'K', 'D', 'S'):
            ns = namespace(arm); modeled = ns['oe'](raw); ns['_limit'] = len(modeled)
            self.assertEqual(ns['od'](modeled), raw)
            prefixes[arm] = ns['lit_prefix'](modeled)
            if arm != 'P':
                frozen = ns['_previous_word_parent_prefix'].__globals__
                self.assertIsNot(frozen['GST'], ns['GST'])
                if arm != 'K': self.assertIsNot(frozen['LIT'], ns['LIT'])
                st = ns['GST']()
                for byte in modeled: st.up(byte)
                self.assertEqual(st.position, len(modeled))
                self.assertEqual(st.completed_words(), (b'Birch', b'Elm'))
                histories[arm] = st.completed_words()
        for arm in ('K', 'D', 'S'): self.assertEqual(prefixes[arm], prefixes['P'])

    def test_standalone_determinism_and_refuse_overwrite(self):
        files = bundle(); self.assertEqual(files, bundle())
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'bundle'; refs = write_bundle(out)
            for name, data in files.items():
                self.assertEqual((out / name).read_bytes(), data)
                self.assertEqual(refs[name]['sha256'], hashlib.sha256(data).hexdigest())
            with self.assertRaises(FileExistsError): write_bundle(out)
            ns = {'__file__': str(out / 'program.py')}
            exec(compile(files['program.py'], str(out / 'program.py'), 'exec'), ns)
            raw = b'First word First word\x00'
            self.assertLessEqual(len(raw), 4096)
            arc = ns['compress'](raw)
            self.assertEqual(ns['decompress'](arc), raw)
            self.assertEqual(ns['compress'](raw), arc)
            (out / 'v').write_bytes(files['v'] + b'x')
            with self.assertRaises(ValueError):
                exec(compile(files['program.py'], str(out / 'program.py'), 'exec'), {'__file__': str(out / 'program.py')})

    def test_builder_rejects_parent_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); parent = root / PARENT; parent.parent.mkdir(parents=True)
            parent.write_bytes(b'wrong')
            with self.assertRaises(ValueError): bundle(root)


if __name__ == '__main__':
    unittest.main()
