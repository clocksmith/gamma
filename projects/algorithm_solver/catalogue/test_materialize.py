import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from .materialize import read_source


class Materialization(unittest.TestCase):
    def fixture(self, root):
        payload = b'def solve(a): return a\n'; (root/'source.py').write_bytes(payload)
        h = hashlib.sha256(payload).hexdigest()
        selection = {'status':'selected','problem_id':'a','language':'python','implementation':{'status':'qualified','source_sha256':h,'receipt_sha256':'r'}}
        locator = {'problem_id':'a','language':'python','source_sha256':h,'receipt_sha256':'r','universe_sha256':'u','relative_path':'source.py'}
        policy = {'protected_problem_ids':[], 'authorized_problem_ids':['a'], 'universe_sha256':'u', 'source_root':str(root)}
        return selection, locator, policy, payload

    def test_exact_qualified_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            s,l,p,b = self.fixture(Path(directory)); self.assertEqual(read_source(s,l,p), b)

    def test_protection_checked_before_any_open(self):
        with tempfile.TemporaryDirectory() as directory:
            s,l,p,b = self.fixture(Path(directory)); p['protected_problem_ids']=['a']
            with patch('os.open', side_effect=AssertionError('must not open')):
                with self.assertRaises(PermissionError): read_source(s,l,p)

    def test_locator_and_pending_denied_before_open(self):
        with tempfile.TemporaryDirectory() as directory:
            s,l,p,b = self.fixture(Path(directory)); l['problem_id']='other'
            with patch('os.open', side_effect=AssertionError('must not open')):
                with self.assertRaises(ValueError): read_source(s,l,p)

    def test_symlink_escape_and_tampered_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); s,l,p,b = self.fixture(root); (root/'alias').symlink_to(root/'source.py'); l['relative_path']='alias'
            with self.assertRaises(OSError): read_source(s,l,p)
            l['relative_path']='../source.py'
            with self.assertRaises(ValueError): read_source(s,l,p)
            l['relative_path']='source.py'; (root/'source.py').write_bytes(b'changed')
            with self.assertRaises(ValueError): read_source(s,l,p)

    def test_string_allowlist_cannot_authorize_substring(self):
        with tempfile.TemporaryDirectory() as directory:
            s,l,p,b = self.fixture(Path(directory)); p['authorized_problem_ids']='abc'
            with patch('os.open', side_effect=AssertionError('must not open')):
                with self.assertRaises(ValueError): read_source(s,l,p)

    def test_bounded_read(self):
        with tempfile.TemporaryDirectory() as directory:
            s,l,p,b = self.fixture(Path(directory))
            with self.assertRaises(ValueError): read_source(s,l,p,maximum_bytes=2)

if __name__ == '__main__': unittest.main()
