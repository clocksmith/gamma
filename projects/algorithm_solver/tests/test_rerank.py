import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from algsolve.rerank import DopplerReranker, scores_from_output

class RerankTests(unittest.TestCase):
    def output(self, rows):
        return '[progress]\n' + json.dumps({'ok':True,'result':{'output':{'query':'q','ranking':rows}}},indent=2)
    def test_rank_order_is_restored_to_candidate_order(self):
        rows=[{'index':1,'document':'b','score':4.0},{'index':0,'document':'a','score':-2.0}]
        self.assertEqual(scores_from_output(self.output(rows),'q',['a','b']),[-2.,4.])
    def test_duplicate_mismatched_nonfinite_and_failed_output_are_rejected(self):
        valid={'index':0,'document':'a','score':1}
        for rows in [[valid,valid], [dict(valid,document='wrong')], [dict(valid,score=float('nan'))]]:
            with self.assertRaises(ValueError): scores_from_output(self.output(rows),'q',['a'])
        with self.assertRaises(ValueError): scores_from_output('{"ok":false,"result":{}}','q',['a'])
        with self.assertRaises(ValueError): scores_from_output(self.output([valid]),'different',['a'])

    def test_adapter_normalizes_only_outer_whitespace_and_preserves_execution_config(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            cli = root/'cli.js'; cli.touch()
            (root/'manifest.json').write_text(json.dumps({'modelId': 'test'}))
            config = {'inference': {'executionPatch': {'set': []}}}
            adapter = DopplerReranker(cli, root, runtime_config=config)
            original_hash = adapter.runtime_config_sha256
            config['inference']['executionPatch']['set'].append('caller mutation')
            def execute(command, **kwargs):
                request = json.loads(Path(command[command.index('--config')+1]).read_text())['request']
                inference = request['runtimeConfig']['inference']
                self.assertEqual(inference['executionPatch'], {'set': []})
                self.assertEqual(inference['rerank'], {'query': 'q\n q', 'documents': ['a\n b']})
                output = {'query': 'q\n q', 'ranking': [{'index': 0, 'document': 'a\n b', 'score': 2.}]}
                return SimpleNamespace(stdout=json.dumps({'ok': True, 'result': {'output': output}}))
            with patch('algsolve.rerank.subprocess.run', side_effect=execute), patch('algsolve.rerank.LANE_ROOT', root):
                self.assertEqual(adapter(' q\n q\n', ['\na\n b ']), [2.])
            self.assertEqual(adapter.runtime_config_sha256, original_hash)
            self.assertEqual(adapter.runtime_config, {'inference': {'executionPatch': {'set': []}}})
            with self.assertRaises(ValueError):
                DopplerReranker(cli, root, runtime_config={'inference': {'rerank': {'query': 'override'}}})
            with self.assertRaises(ValueError):
                adapter(' \n', ['document'])

if __name__ == '__main__': unittest.main()
