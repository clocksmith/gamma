"""Original JS function toy records checked by independent Python semantics."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest
HERE=Path(__file__).resolve().parent
S=importlib.util.spec_from_file_location('q_js_integration_host',HERE/'host_check.py');checker=importlib.util.module_from_spec(S);S.loader.exec_module(checker)
class IntegrationTests(unittest.TestCase):
    def test_all_js_official_function_routes_and_negative_records(self):
        node=os.environ.get('NODE_BIN') or shutil.which('node')
        if not node:self.skipTest('existing Node unavailable; no installation')
        process=subprocess.run([node,str(HERE/'toy_records.cjs')],capture_output=True,check=True,timeout=20)
        rows=[json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual({row['pid'] for row in rows if row['accepted']},set(checker.METHODS))
        self.assertEqual(len(rows),17)
        for row in rows:
            result=checker.check_observation(row['pid'],row['args'],row['record'],'javascript')
            self.assertEqual(result[0],row['accepted'],(row['label'],result))
if __name__=='__main__':unittest.main()
