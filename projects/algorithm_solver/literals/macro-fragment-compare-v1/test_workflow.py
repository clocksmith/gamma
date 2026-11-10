"""Portable exact-source workflow checks; no private source or service access."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run


class WorkflowTest(unittest.TestCase):
    def test_help_needs_no_compact_transformer_or_source_service(self):
        for name in ('run.py', 'verify.py', 'report.py'):
            result = subprocess.run([sys.executable, str(HERE / name), '--help'],
                                    text=True, capture_output=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('usage:', result.stdout)

    def test_missing_diagnostic_refuses_with_actionable_error_before_source_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(run, 'HERE', Path(tmp) / 'comparison'):
                with self.assertRaisesRegex(FileNotFoundError, '--exact-only'):
                    run.load_transform()

    def test_fragment_evaluation_reuses_prepared_dictionary_and_preserves_packets(self):
        sources = {'1': 'return x + 1;', '2': 'return café + 2;', '3': ''}
        for width in (6, 7, 8):
            words = ['return ', ' + ', ';\n']
            words.extend(f'~unused-{i}~' for i in range((1 << width) - 1 - len(words)))
            table = [(word.encode(),) for word in words]
            with patch.object(run.FSP, 'FragmentEncoder', wraps=run.FSP.FragmentEncoder) as factory:
                report, _ = run.evaluate(sources, table, width, {}, 'fragment')
                self.assertEqual(factory.call_count, 1)
            for row in report['rows']:
                packet = run.FSP.encode(sources[str(row['id'])], words, width)
                binary = run.FSP.packet_bytes(packet)
                self.assertEqual(row['packet_sha256'], run.sha(binary))
                self.assertEqual(row['packet_bits'], len(binary) * 8)
                self.assertEqual(row['spelling_payload_bits'], packet.spelling_bits)

    def test_renderer_preserves_historical_report_and_supports_explicit_exact_only(self):
        # Existing aggregate evidence contains hashes/costs, never source bytes.
        original = json.loads((HERE / 'results.json').read_bytes())
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            output = tmp / 'historical.md'
            result = subprocess.run([sys.executable, str(HERE / 'report.py'), '--output', str(output)],
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_bytes(), (HERE / 'RESULTS.md').read_bytes())
            original['languages']['python'].pop('compact_static_diagnostic')
            original['contract']['compact_diagnostic'] = 'omitted_by_request'
            path = tmp / 'exact-only.json'
            path.write_text(json.dumps(original))
            result = subprocess.run([sys.executable, str(HERE / 'report.py'), '--results', str(path),
                                     '--output', str(output)], capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Not run: this exact-source-only comparison', output.read_text())
            original['contract'].pop('compact_diagnostic')
            path.write_text(json.dumps(original))
            result = subprocess.run([sys.executable, str(HERE / 'report.py'), '--results', str(path),
                                     '--output', str(output)], capture_output=True, text=True, timeout=20)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Missing compact diagnostic', result.stderr)


if __name__ == '__main__':
    unittest.main()
