"""Public packaging tests; fake sources exercise disclosure boundaries, not accuracy."""
import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock
import numpy as np
from projects.algorithm_solver.algsolve import export_bits_browser as exporter


class BrowserExportTests(unittest.TestCase):
    def test_export_limits_fields_and_keeps_title_only_documents_closed(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            public = root/'public'
            bits = public/'labs/two-button'
            (bits/'problems').mkdir(parents=True)
            packet = json.dumps({'source': {'attribution': ['https://example.org/a'], 'license': ['test attribution'],
                                          'private': 'never copy'}, 'private_tests': 'never copy'}).encode()
            (bits/'problems/a.json').write_bytes(packet)
            (bits/'problems/manifest.json').write_text('{}')
            for name in ['keys', 'vectors']:
                (root/name).write_bytes(b'fixture')
            variants = {}
            for role in ['embedding', 'rerank']:
                manifest = {'modelId': role, 'hashAlgorithm': 'sha256', 'shards': [{'size': 2}]}
                path = root/(role+'.json');path.write_text(json.dumps(manifest))
                variants[role] = {'manifestPath': str(path), 'manifestHash': hashlib.sha256(path.read_bytes()).hexdigest(),
                                  'manifestVariantId': role+'-sha256-v1', 'weightsBaseUrl': 'https://example.org/'+role,
                                  'tokenizer': {'sha256': 'f'*64, 'size': 2}}
            (root/'variants.json').write_text(json.dumps(variants))
            matrix = np.zeros((2, 1024), dtype=np.float32);matrix[:, 0] = 1
            fake = SimpleNamespace(keys=['lc:a', 'lc:b'], bits=bits, vectors=matrix,
                metadata={f'lc:{s}': {'slug': s, 'title': s.upper(), 'problem_id': 'leetcode:'+str(i), 'difficulty': 'Easy'} for i, s in enumerate(['a','b'],1)},
                manifest={'problems': {'a': {'sha256': hashlib.sha256(packet).hexdigest()}}},
                document=lambda key: ('permitted description', 'published-statement') if key=='lc:a' else ('B', 'title-only'))
            with mock.patch.object(exporter, 'BitsRecognizer', return_value=fake), mock.patch.object(exporter.subprocess, 'check_output', return_value='a'*40):
                result = exporter.export_bundle(public_root=public, keys=root/'keys', vectors=root/'vectors', gate=root/'gate', gate_sha256='1'*64, doppler_root=root, output=root/'output', model_variants=root/'variants.json')
            rows = json.loads((root/'output/documents.json').read_text())
            assert result['count']==2 and result['titleOnlyCount']==1
            assert rows[1]['description']=='B'
            assert rows[0]['notices']['license']==['test attribution']
            for path in (root/'output').rglob('*.json'):
                assert 'never copy' not in path.read_text()
                assert tmp not in path.read_text()
            assert (root/'output/vectors.f32').stat().st_size==2*1024*4
            manifest = json.loads((root/'output/manifest.json').read_text())
            assert manifest['policy']['recognitionQualified'] is False
            assert manifest['policy']['scoring']=='yes-minus-no'
            assert manifest['models'][0]['manifest']['url']=='models/embedding/manifest.json'
