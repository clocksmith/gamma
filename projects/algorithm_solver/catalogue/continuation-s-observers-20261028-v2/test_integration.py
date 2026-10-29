"""Cross-language synthetic records against independent S owner contracts."""
import importlib.util
import json
from pathlib import Path
import os
import shutil
import subprocess
import unittest
ROOT=Path(__file__).parent
_SPEC=importlib.util.spec_from_file_location('s_cross_toy_host',ROOT/'host_check.py');host=importlib.util.module_from_spec(_SPEC);_SPEC.loader.exec_module(host)
class Integration(unittest.TestCase):
    def test_javascript_source_free_records(self):
        node=os.environ.get('NODE_BINARY') or shutil.which('node')
        if not node:self.skipTest('existing Node runtime unavailable')
        output=subprocess.run([node,str(ROOT/'test_observers.cjs'),'--records'],check=True,capture_output=True,text=True,timeout=20)
        payload=json.loads(output.stdout);self.assertEqual(payload['tests'],17);self.assertEqual({row['pid'] for row in payload['records']},set(host.IDS))
        for row in payload['records']:
            self.assertEqual(host.check_observation(row['pid'],row['args'],row['record'],'javascript'),(True,None))
            forged=json.loads(json.dumps(row['record']));forged['entry_integrity']['original_export_unchanged']=False
            self.assertFalse(host.check_observation(row['pid'],row['args'],forged,'javascript')[0])
if __name__=='__main__':unittest.main()
