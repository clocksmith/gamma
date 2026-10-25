import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from . import runtime_identity as identity


class RuntimeIdentity(unittest.TestCase):
    def test_exact_identity_and_drift_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            interpreter=Path(directory)/'python';interpreter.write_bytes(b'synthetic interpreter identity')
            node={'node_sha256':'a'*64};runtime={'python_executable_sha256':hashlib.sha256(interpreter.read_bytes()).hexdigest(),'sandbox_sha256':hashlib.sha256(Path(identity.sandbox.__file__).read_bytes()).hexdigest(),'limits':{'cpu_seconds':3,'wall_seconds':8,'memory_bytes':1073741824,'max_output_bytes':4194304}}
            with patch.object(identity.pinned_runtime,'freeze_runtime',return_value=node):
                r=identity.attest({'a':{'runtime':{'manifest':node}}},{'a':{'runtime':runtime}},'unused',interpreter)
                self.assertTrue(r['current_recorded_runtime_identity_matches']);self.assertFalse(r['source_execution_performed']);self.assertFalse(r['current_full_serving_release_qualified'])
                runtime['python_executable_sha256']='b'*64
                with self.assertRaises(ValueError):identity.attest({'a':{'runtime':{'manifest':node}}},{'a':{'runtime':runtime}},'unused',interpreter)
                with self.assertRaises(ValueError):identity.attest({'a':{'runtime':{'manifest':{}}}},{},'unused',interpreter)

if __name__=='__main__':unittest.main()
