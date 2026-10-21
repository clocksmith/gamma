import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from inventory import build, render


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def manifest(self, label, records):
        root = self.root / label
        root.mkdir()
        rows = []
        for problem, language, data in records:
            name = str(problem) + ('.js' if language == 'javascript' else '.py')
            (root / name).write_bytes(data)
            rows.append({'id': problem, 'language': language, 'path': name,
                         'sha256': hashlib.sha256(data).hexdigest()})
        path = root / 'manifest.json'
        path.write_text(json.dumps({'source_inventory': rows}))
        return path

    def test_occurrences_are_not_distinct_problems(self):
        p = self.manifest('a', [(1, 'python', b'x = 0\nx = 0\n'), (2, 'python', b'x = 0\n')])
        w = build([p])['witnesses'][0]
        self.assertEqual((w['occurrence_count'], w['distinct_problem_count']), (3, 2))
        self.assertEqual([x['line'] for x in w['occurrences']], [1, 2, 1])

    def test_single_problem_not_reuse(self):
        p = self.manifest('a', [(1, 'python', b'x = 0\nx = 0\n')])
        self.assertEqual(build([p])['witnesses'], [])

    def test_cross_language_separation(self):
        p = self.manifest('a', [(1, 'python', b'pass\n'), (2, 'javascript', b'pass\n')])
        self.assertEqual(build([p])['witnesses'], [])

    def test_whitespace_and_newlines(self):
        p = self.manifest('a', [(1, 'python', b'  x = 0\r\nx = 0 \r\n\r\n'),
                                (2, 'python', b'  x = 0\rx = 0\n')])
        w = build([p])['witnesses']
        self.assertEqual([x['literal'] for x in w], ['  x = 0'])

    def test_determinism(self):
        a = self.manifest('a', [(1, 'python', b'x = 0')])
        b = self.manifest('b', [(2, 'python', b'x = 0\n')])
        self.assertEqual(render(build([a, b])), render(build([b, a])))

    def test_hash_mismatch(self):
        p = self.manifest('a', [(1, 'python', b'x = 0')])
        (p.parent / '1.py').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'digest mismatch'):
            build([p])

    def test_duplicate_identity_rejected(self):
        a = self.manifest('a', [(1, 'python', b'x = 0')])
        b = self.manifest('b', [(1, 'python', b'x = 0')])
        with self.assertRaisesRegex(ValueError, 'Duplicate language'):
            build([a, b])

    def test_path_escape_rejected(self):
        p = self.manifest('a', [(1, 'python', b'x = 0')])
        d = json.loads(p.read_text())
        d['source_inventory'][0]['path'] = '../1.py'
        p.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError, 'Unsafe source'):
            build([p])

    def test_same_path_cannot_create_second_problem(self):
        p = self.manifest('a', [(1, 'python', b'x = 0')])
        d = json.loads(p.read_text())
        d['source_inventory'].append(dict(d['source_inventory'][0], id=2))
        p.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError, 'filename must match'):
            build([p])

    def test_noninteger_ids_rejected(self):
        for value in [True, 1.9, '1']:
            with self.subTest(value=value):
                p = self.manifest(str(value), [(1, 'python', b'x = 0')])
                d = json.loads(p.read_text())
                d['source_inventory'][0]['id'] = value
                p.write_text(json.dumps(d))
                with self.assertRaisesRegex(ValueError, 'must be an integer'):
                    build([p])


if __name__ == '__main__':
    unittest.main()
