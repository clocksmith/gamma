import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from .recognition_assets import inspect_assets, DEFAULT_EMBEDDING_DIR


class RecognitionAssetsTests(unittest.TestCase):
    def test_exact_override_and_no_array_or_model_load(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('model.safetensors', 'tokenizer.json', 'config.json'):
                (root/name).write_text('{}')
            (root/'data'/'derived').mkdir(parents=True)
            (root/'data'/'derived'/'corpus_embeddings.npy').write_text('not an array')
            with patch.dict(os.environ, {'ALGSOLVE_EMBEDDING_DIR':directory}):
                report=inspect_assets(root)
            self.assertEqual(report['root_resolution'],'ALGSOLVE_EMBEDDING_DIR')
            self.assertEqual(report['model_assets']['model.safetensors']['bytes'],2)
            self.assertNotIn('sha256',report['model_assets']['model.safetensors'])
            self.assertIn('sha256',report['model_assets']['config.json'])
            self.assertFalse(report['model_assets']['config.json']['hash_verified'])
            self.assertTrue(report['index_artifacts']['corpus_embeddings.npy']['exists'])
            self.assertFalse(report['index_payload_loaded']); self.assertFalse(report['model_imported'])

    def test_wrong_hash_is_not_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'model.safetensors').write_bytes(b'synthetic')
            with patch.dict(os.environ,{'ALGSOLVE_EMBEDDING_DIR':directory}):
                report=inspect_assets(root,verify_model_hashes=True)
            record=report['model_assets']['model.safetensors']
            self.assertEqual(record['hash_status'],'computed');self.assertFalse(record['hash_verified'])
            self.assertFalse(report['model_assets']['tokenizer.json']['exists'])
            self.assertFalse(report['current_serving_release_qualified'])

    def test_default_resolution_matches_pinned_code_without_scanning(self):
        with patch.dict(os.environ,{},clear=True), patch('projects.algorithm_solver.catalogue.recognition_assets._inspect',return_value={'exists':False}) as inspect:
            report=inspect_assets('/synthetic/lane')
        self.assertEqual(report['embedding_root'],DEFAULT_EMBEDDING_DIR)
        self.assertEqual(inspect.call_count,9)
        paths=[str(call.args[0]) for call in inspect.call_args_list]
        self.assertTrue(all(p.startswith(DEFAULT_EMBEDDING_DIR+'/') or p.startswith('/synthetic/lane/data/derived/') for p in paths))


if __name__=='__main__':unittest.main()
