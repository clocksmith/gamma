import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import fx2_wrt_support_deploy_fixture_v1 as runner
from tools.fx2_wrt_support_deploy_adapter_v1 import build,PARENT


class DeploymentTests(unittest.TestCase):
    def test_deterministic_delivery_and_exclusive_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);work=root/'work';work.mkdir();p=work/'source.cpp';p.write_bytes(b'\0\r\ninvalid\xff')
            runner.write_bundle(root/'a.zip',work,[p],'literal options\n')
            runner.write_bundle(root/'b.zip',work,[p],'literal options\n')
            self.assertEqual((root/'a.zip').read_bytes(),(root/'b.zip').read_bytes())
            with self.assertRaises(FileExistsError):runner.write_bundle(root/'a.zip',work,[p],'x')
            with zipfile.ZipFile(root/'a.zip') as z:
                self.assertEqual(z.read('source.cpp'),p.read_bytes());self.assertEqual(z.read('invocation-and-build.txt'),b'literal options\n')
                self.assertTrue(all(i.date_time==(1980,1,1,0,0,0) for i in z.infolist()))

    def test_exact_adapter_and_no_diagnostic_includes(self):
        x=build();self.assertEqual(x,json.loads((ROOT/runner.ADAPTER).read_text()))
        for row in x['files']:
            text=(PARENT/row['source_path']).read_text()
            for change in row['replacements']:
                self.assertEqual(text.count(change['before']),1);text=text.replace(change['before'],change['after'])
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),row['patched_sha256'])
            self.assertEqual(text.count('p_->Predict()'),1);self.assertEqual(text.count('p_->Perceive(bit)'),1)
            self.assertNotIn('gamma-coder-trace',text)
        self.assertNotIn('GAMMA_FX2_', (ROOT/'lib/wrt_support_deploy_v1.hpp').read_text())

    def test_changed_engine_rejected(self):
        with patch.object(runner,'ENGINE_SHA','0'*64):
            with self.assertRaises(ValueError):runner.engine()


if __name__=='__main__':unittest.main()
