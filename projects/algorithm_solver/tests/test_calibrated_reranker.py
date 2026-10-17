import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from algsolve import calibrated_reranker as loader
from algsolve.rerank_recognition import calibrate, digest


class CalibratedRerankerTests(unittest.TestCase):
    def test_recomputed_fit_runtime_and_input_identity_are_required(self):
        with TemporaryDirectory() as temp:
            root = Path(temp); source = root/'bound'; source.write_text('source')
            query = {'qid': 'd', 'kind': 'exact', 'target': 'a'}
            rows = [{**query, 'reranked': [{'key':'a','score':2.}, {'key':'b','score':0.}]}]
            contract = {'dev_queries': [query], 'runtime_config': {}, 'runtime_config_sha256': 'cfg',
                        'model_manifest_sha256': 'model', 'model_id': 'm', 'runtime_revision': 'revision',
                        'files': {'bound': hashlib.sha256(source.read_bytes()).hexdigest()}}
            calibration = {'binding': digest(contract), 'dev_rows_sha256': digest(rows),
                           'thresholds': calibrate(rows, [query])}
            for name, value in [('contract.json', contract), ('calibration.json', calibration)]:
                (root/name).write_text(json.dumps(value))
            (root/'dev.jsonl').write_text(json.dumps(rows[0])+'\n')
            reranker = SimpleNamespace(cli=root/'runtime/src/cli/tool.js', manifest_sha256='model',
                                       model_id='m', runtime_config_sha256='cfg')
            with patch.object(loader, 'LANE_ROOT', root), patch.object(loader, 'DopplerReranker', return_value=reranker):
                with patch.object(loader.subprocess, 'check_output', side_effect=['revision\n', '']):
                    self.assertEqual(loader.load(root, Path('cli'), root), (reranker, calibration['thresholds']))
                with patch.object(loader.subprocess, 'check_output', side_effect=['revision\n', ' M source.js']):
                    with self.assertRaisesRegex(ValueError, 'runtime differs'):
                        loader.load(root, Path('cli'), root)
                source.write_text('changed')
                with self.assertRaisesRegex(ValueError, 'input changed'):
                    loader.load(root, Path('cli'), root)
                source.write_text('source')
                calibration['thresholds']['min_score'] = -100
                (root/'calibration.json').write_text(json.dumps(calibration))
                with self.assertRaisesRegex(ValueError, 'development fit'):
                    loader.load(root, Path('cli'), root)


if __name__ == '__main__':
    unittest.main()
