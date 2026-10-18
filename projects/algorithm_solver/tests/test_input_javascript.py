import hashlib
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from algsolve.input_javascript import fit, lexemes, read_development, reserve
from algsolve.input_vocabulary import codes, encode


class JavaScriptInputTests(unittest.TestCase):
    def test_reservation_keeps_siblings_and_duplicate_sources_out_of_fitting(self):
        allowed = {str(i): SimpleNamespace(key=f'lc:p{i}', slug=f'p{i}', tags=['Array']) for i in range(20)}
        allowed['20'] = SimpleNamespace(key='lc:p0-ii', slug='p0-ii', tags=['Array'])
        files = [{'path': f'solution/{i}.Title/Solution.js', 'sha256': str(i)} for i in range(21)]
        rows, selected, _ = reserve(files, allowed, 5)
        self.assertEqual(len({r['family'] for r in selected}), 5)
        family_split = {}
        for row in rows:
            self.assertEqual(family_split.setdefault(row['family'], row['split']), row['split'])
        protected_hash = selected[0]['sha256']
        train = next(r for r in rows if r['split'] == 'train')
        for file in files:
            if file['path'] == train['path']:
                file['sha256'] = protected_hash
        rows, _, excluded = reserve(files, allowed, 5)
        self.assertTrue(any(r['path'] == train['path'] for r in excluded))
        self.assertFalse(any(r['split'] != 'confirmation' and r['sha256'] == protected_hash for r in rows))
        self.assertEqual(reserve(files[::-1], allowed, 5)[1], reserve(files, allowed, 5)[1])

    def test_protected_text_is_never_opened_and_source_drift_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            text = b'const value = 1;'
            (root / 'one.js').write_bytes(text)
            rows = [{'path': 'absent-confirmation.js', 'sha256': 'do-not-read', 'split': 'confirmation'}]
            rows += [{'path': 'one.js', 'sha256': hashlib.sha256(text).hexdigest(), 'split': split}
                     for split in ['train', 'development']]
            with patch('algsolve.input_javascript.subprocess.run', return_value=SimpleNamespace(returncode=0)):
                accepted, rejected = read_development(root, rows, 'node')
                self.assertEqual(len(accepted), 2)
                self.assertEqual(rejected, [])
                (root / 'one.js').write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                    read_development(root, rows, 'node')

    def test_shared_shortcuts_and_round_trip_cost(self):
        rows = [{'family': str(i), 'text': f'const value = {i}; return value === 2; // bespokeComment\n'}
                for i in range(3)]
        rows[0]['text'] += 'bespokeIdentifier ' * 100
        weights, support = fit(rows, 64)
        self.assertNotIn('bespokeIdentifier', support)
        self.assertNotIn('bespokeComment', support)
        self.assertIn('===', support)
        book = codes(weights)
        for row in rows:
            presses, counts = encode(row['text'], book)
            self.assertEqual(presses, sum(len(book[t]) * n for t, n in counts.items()))
        self.assertEqual(lexemes('"hidden" `alsoHidden` /* comment */ value === other'), ['value', '===', 'other'])


if __name__ == '__main__':
    unittest.main()
