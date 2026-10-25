import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import zipfile

from .provision_encoder import budget, download_one, inspect_wheels, pinned


class ProvisionEncoderTests(unittest.TestCase):
    def test_existing_exact_artifact_is_reused_without_network(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'model').mkdir();(root/'model'/'x').write_bytes(b'abc')
            row={'name':'x','folder':'model','bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest()}
            with patch('projects.algorithm_solver.catalogue.provision_encoder.urlopen',side_effect=AssertionError):
                download_one(root,row)
            row['sha256']='0'*64
            with self.assertRaises(ValueError):download_one(root,row)

    def test_manifest_and_budget_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'manifest';p.write_text('{}')
            with self.assertRaises(ValueError):pinned(p,'0'*64)
            with patch('projects.algorithm_solver.catalogue.provision_encoder.CAP',1):
                with self.assertRaises(RuntimeError):budget(root,1)

    def test_wheel_sizes_and_notices_are_inspected_without_execution(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'wheels').mkdir();p=root/'wheels'/'synthetic.whl'
            with zipfile.ZipFile(p,'w')as z:z.writestr('sample.py','raise AssertionError()');z.writestr('sample.dist-info/LICENSE','synthetic')
            row={'name':p.name,'folder':'wheels','bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            result=inspect_wheels(root,[row]);self.assertEqual(result['wheel_count'],1);self.assertEqual(len(result['license_notice_members']),1)

    def test_unsafe_wheel_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'wheels').mkdir();p=root/'wheels'/'bad.whl'
            with zipfile.ZipFile(p,'w')as z:z.writestr('../escape','bad')
            row={'name':p.name,'folder':'wheels','bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            with self.assertRaises(ValueError):inspect_wheels(root,[row])


if __name__=='__main__':unittest.main()
