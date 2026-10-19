"""Catalog environment identities fail closed on executable or stdlib drift."""
import copy
import unittest
from unittest.mock import patch
from algsolve.qualification_environment import capture,verify


class QualificationEnvironmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.actual=capture()

    def test_actual_judge_environment_verifies(self):
        verify(self.actual)
        self.assertEqual([r['path'] for r in self.actual['executables']],
                         ['/usr/bin/python3','/usr/bin/bwrap','/usr/bin/prlimit'])
        self.assertGreater(len(self.actual['stdlib_files_sha256']),100)

    def test_binary_version_stdlib_and_extra_fields_cannot_drift(self):
        variants=[]
        changed=copy.deepcopy(self.actual);changed['executables'][0]['sha256']='0'*64;variants.append(changed)
        changed=copy.deepcopy(self.actual);changed['interpreter']['version']='different';variants.append(changed)
        changed=copy.deepcopy(self.actual);changed['stdlib_files_sha256']['json/__init__.py']='0'*64;variants.append(changed)
        changed=copy.deepcopy(self.actual);changed['extra']='unrecognized';variants.append(changed)
        for expected in variants:
            with self.subTest(expected=expected.keys()),patch('algsolve.qualification_environment.capture',return_value=self.actual),self.assertRaisesRegex(ValueError,'environment changed'):
                verify(expected)

    def test_manifest_never_selects_an_executable(self):
        expected=copy.deepcopy(self.actual);expected['executables'][0]['path']='/tmp/untrusted-command'
        with patch('algsolve.qualification_environment.capture',return_value=self.actual),self.assertRaises(ValueError):verify(expected)
        with patch('algsolve.qualification_environment.capture') as mocked,self.assertRaises(ValueError):verify({'schema':'unknown'})
        mocked.assert_not_called()

    def test_catalog_load_enforces_optional_environment_and_preserves_legacy(self):
        import hashlib
        import tempfile
        from pathlib import Path
        from algsolve.approved_library import ApprovedLibrary,build
        from test_approved_library import fixture
        e,inv,rows=fixture()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'runtime.py').write_text('fixed source')
            files={'runtime.py':hashlib.sha256(b'fixed source').hexdigest()}
            legacy=ApprovedLibrary(build([e],inv,rows,evidence={},runtime_files=files))
            legacy.verify_runtime(root)
            good=ApprovedLibrary(build([e],inv,rows,evidence={},runtime_files=files,runtime_environment=self.actual))
            good.verify_runtime(root)
            changed=copy.deepcopy(self.actual);changed['executables'][0]['sha256']='0'*64
            bad=ApprovedLibrary(build([e],inv,rows,evidence={},runtime_files=files,runtime_environment=changed))
            with self.assertRaisesRegex(ValueError,'environment changed'):bad.verify_runtime(root)
