"""Unpinned reporter regression: JSON layout is distinct from source identity."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('stack_reference_report', Path(__file__).with_name('report.py'))
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class ReferenceIdentityTests(unittest.TestCase):
    def fixture(self, work):
        sources = {'2': 'function solve(a){return a+2;}', '1': 'function solve(a){return a+1;}'}
        vocab = ['function solve(', 'a', ')', '{', 'return ', '+', '1', '2', ';', '}']
        c = {'references': {'R': 'refR', 'seed13': 'ref13', 'best24': 'ref24'}, 'private_files': {}}
        for ref in c['references'].values():
            (work/ref).mkdir()
            for filename, value in (('sources.json', sources), ('dictionary.json', vocab)):
                original = json.dumps(value, separators=(',', ':')).encode()
                (work/ref/filename).write_bytes(original)
                c['private_files'][ref+'/'+filename] = hashlib.sha256(original).hexdigest()
        return sources, vocab, c

    def test_different_json_key_order_and_layout_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory); sources, vocab, c = self.fixture(work)
            source_artifact = json.dumps(sources, indent=2, sort_keys=True).encode()
            vocab_artifact = json.dumps(vocab, indent=2).encode()
            self.assertNotEqual(hashlib.sha256(source_artifact).hexdigest(), c['private_files']['refR/sources.json'])
            for name in ('R', 'seed13', 'best24'):
                report.verify_reference_inputs(name, source_artifact, vocab_artifact, c, work)

    def test_changed_source_string_and_vocabulary_order_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory); sources, vocab, c = self.fixture(work)
            changed = {**sources, '1': sources['1']+' '}
            with self.assertRaises(AssertionError):
                report.verify_reference_inputs('R', json.dumps(changed).encode(), json.dumps(vocab).encode(), c, work)
            with self.assertRaises(AssertionError):
                report.verify_reference_inputs('R', json.dumps(sources).encode(), json.dumps(list(reversed(vocab))).encode(), c, work)

    def test_wrong_pinned_hash_or_changed_original_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory); sources, vocab, c = self.fixture(work)
            source_artifact, vocab_artifact = json.dumps(sources).encode(), json.dumps(vocab).encode()
            rel = 'refR/sources.json'; old_hash = c['private_files'][rel]
            c['private_files'][rel] = '0'*64
            with self.assertRaises(AssertionError):
                report.verify_reference_inputs('R', source_artifact, vocab_artifact, c, work)
            c['private_files'][rel] = old_hash
            # Even harmless original JSON reformatting fails its original seal.
            (work/rel).write_bytes(source_artifact)
            with self.assertRaises(AssertionError):
                report.verify_reference_inputs('R', source_artifact, vocab_artifact, c, work)

    def test_legacy_no_work_call_requires_exact_pinned_serialization(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory); sources, vocab, c = self.fixture(work)
            report.verify_reference_inputs('R', (work/'refR/sources.json').read_bytes(), (work/'refR/dictionary.json').read_bytes(), c)
            with self.assertRaises(AssertionError):
                report.verify_reference_inputs('R', json.dumps(sources, sort_keys=True).encode(), json.dumps(vocab).encode(), c)


if __name__ == '__main__':
    unittest.main()
