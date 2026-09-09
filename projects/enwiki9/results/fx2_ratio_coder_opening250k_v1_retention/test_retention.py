import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('retention', Path(__file__).with_name('retain.py'))
retention = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retention)


class RetentionTests(unittest.TestCase):
    def test_closed_chunks_reconstruct_and_identical_traces_share_objects(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / 'run'
            run.mkdir()
            (root / 'operations/adaptive/completed').mkdir(parents=True)
            (root / 'operations/adaptive/completed' / (retention.JOB_ID + '.json')).write_text(json.dumps(dict(
                execution_resources=dict(cleanup_complete=True, guard_path='guard.json'))))
            (root / 'guard.json').write_text(json.dumps(dict(status='complete', returncode=0)))
            (run / 'stage-decision.json').write_text(json.dumps(dict(status='passed', correctness_pass=True)))
            raw = bytes(range(256)) * 33 + b'partial'
            for name in ('encode.ratio', 'decode.ratio'):
                (run / name).write_bytes(raw)
            (run / 'archive.bin').write_bytes(b'exact archive')
            with patch.multiple(retention, ROOT=root, RUN=run, OUT=root / 'retained', CHUNK=4096):
                rows = [retention.binding(p) for p in sorted(run.iterdir())]
                (run / 'artifacts.json').write_text(json.dumps(dict(files=rows)))
                retention.main()
                receipt = json.loads((root / 'receipt.json').read_text())
                self.assertEqual(receipt['unique_trace_count'], 1)
                self.assertEqual(len(receipt['raw_traces']), 2)
                chunks = receipt['raw_traces'][0]['chunks']
                self.assertEqual(len(chunks), 3)
                self.assertEqual(chunks, receipt['raw_traces'][1]['chunks'])
                restored = b''.join(retention.gzip.decompress((root / c['gzip']['path']).read_bytes()) for c in chunks)
                self.assertEqual(restored, raw)
                self.assertEqual([c['offset'] for c in chunks], [0, 4096, 8192])
                self.assertEqual((run / 'encode.ratio').read_bytes(), raw)
                with self.assertRaises(FileExistsError):
                    retention.main()

    def test_missing_terminal_job_refuses_before_output_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.multiple(retention, ROOT=root, RUN=root / 'live', OUT=root / 'retained'):
                with self.assertRaisesRegex(ValueError, 'completed job'):
                    retention.main()
                self.assertFalse((root / 'retained').exists())


if __name__ == '__main__':
    unittest.main()
