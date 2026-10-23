"""Activation payload and runtime drift checks; no activation or private reads."""
import ast
import copy
from pathlib import Path
import sys
import tempfile
import tokenize
import unittest
from unittest.mock import patch
import common
import make_contract

class ContractTests(unittest.TestCase):
    def test_only_authorization_changes_after_exact_review_match(self):
        reviewed={'execution_authorized':False,'code_hashes':{'example.py':'abc'},'runtime_files':{}}
        with patch.object(make_contract,'verify') as verify:
            result=make_contract.activation_payload(copy.deepcopy(reviewed),reviewed)
            verify.assert_called_once_with(reviewed)
        self.assertEqual(result,{**reviewed,'execution_authorized':True});self.assertFalse(reviewed['execution_authorized'])
    def test_dependency_receipt_input_or_runtime_repin_requires_new_review(self):
        for field in ('code_hashes','runtime_files','qualification','inputs'):
            reviewed={'execution_authorized':False,field:{'pin':'old'}};current=copy.deepcopy(reviewed);current[field]['pin']='changed'
            with self.subTest(field=field),patch.object(make_contract,'verify'):
                with self.assertRaisesRegex(AssertionError,'pending contract drift'):make_contract.activation_payload(current,reviewed)
    def test_identical_manifest_still_detects_runtime_byte_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'inherited-runtime';path.write_bytes(b'reviewed')
            c={'execution_authorized':False,'runtime_files':{**common.renderer_runtime_files(),str(path):common.sha(path.read_bytes())}}
            path.write_bytes(b'changed')
            with patch.object(make_contract,'verify',side_effect=common.verify_runtime_files):
                with self.assertRaises(AssertionError):make_contract.activation_payload(copy.deepcopy(c),c)
    def test_builder_pins_renderer_stdlib_and_resolved_interpreter(self):
        c=make_contract.build()
        for path in (Path(ast.__file__).resolve(),Path(tokenize.__file__).resolve(),Path(sys.executable).resolve()):
            self.assertEqual(c['runtime_files'][str(path)],common.sha(path.read_bytes()))
        self.assertFalse(c['execution_authorized']);self.assertFalse(c['prelaunch_private_content_read'])
        missing=copy.deepcopy(c);del missing['runtime_files'][str(Path(ast.__file__).resolve())]
        with self.assertRaisesRegex(AssertionError,'renderer runtime pin missing'):common.verify_runtime_files(missing)

if __name__=='__main__':unittest.main()
