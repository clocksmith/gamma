"""Validate this cohort's study.record.v1 records against the problem_catalogue schema.

Checks every record with jsonschema, every Ref (path, sha256, kind/id/version of the target),
every FileRef (sha256 and bytes), every SourcePointer (sha256 and JSON selector), and that manifest.json and
SHA256SUMS list each record. Run: python3 test_study_records.py
"""
import hashlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
GAMMA = HERE.parents[4]
SCHEMA = json.loads((GAMMA / 'projects/problem_catalogue/schema.v1.json').read_text())
RECORDS = HERE / 'study-records'
REF_KEYS = {'kind', 'id', 'version', 'path', 'sha256'}
FILE_KEYS = {'path', 'sha256', 'bytes', 'mediaType'}
POINTER_KEYS = {'repository', 'revision', 'path', 'sha256', 'selector'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from nodes(child)


class StudyRecords(unittest.TestCase):
    def setUp(self):
        self.files = sorted(RECORDS.glob('*.json'))
        self.records = {p.name: json.loads(p.read_text()) for p in self.files}

    def test_records_exist_and_are_named_by_id(self):
        self.assertEqual(len(self.files), 35)
        for name, record in self.records.items():
            self.assertEqual(name, record['kind'] + '--' + record['id'].replace(':', '_') + '.json')
            self.assertEqual((record['schema'], record['version']), ('study.record.v1', 1))
            self.assertNotIn(record['kind'], ('evidence', 'admission'))

    def test_schema(self):
        for name, record in self.records.items():
            definition = record['kind'].title().replace('-', '')
            validator = Draft202012Validator({**SCHEMA, 'oneOf': [{'$ref': '#/$defs/' + definition}]})
            errors = sorted(validator.iter_errors(record), key=str)
            self.assertFalse(errors, name + ': ' + (errors[0].message if errors else ''))

    def test_hashes(self):
        refs = files = pointers = 0
        for name, record in self.records.items():
            for node in nodes(record):
                keys = set(node)
                if keys == REF_KEYS:
                    target = GAMMA / node['path']
                    self.assertEqual(sha(target.read_bytes()), node['sha256'], name + ' -> ' + node['path'])
                    value = json.loads(target.read_text())
                    self.assertEqual((value['kind'], value['id'], value['version']), (node['kind'], node['id'], node['version']))
                    refs += 1
                elif keys == FILE_KEYS:
                    raw = (GAMMA / node['path']).read_bytes()
                    self.assertEqual((sha(raw), len(raw)), (node['sha256'], node['bytes']), name + ' -> ' + node['path'])
                    files += 1
                elif keys == POINTER_KEYS:
                    self.assertEqual(node['repository'], 'gamma')
                    raw = (GAMMA / node['path']).read_bytes()
                    self.assertEqual(sha(raw), node['sha256'], name + ' -> ' + node['path'])
                    if node['selector']:
                        current = json.loads(raw)
                        for part in node['selector'].lstrip('/').split('/'):
                            current = current[int(part)] if isinstance(current, list) else current[part]
                    pointers += 1
        self.assertGreater(refs, 0)
        self.assertGreater(files, 0)
        self.assertGreater(pointers, 0)

    def test_listed_in_manifest_and_sums(self):
        manifest = {f['path']: f['sha256'] for f in json.loads((HERE / 'manifest.json').read_text())['files']}
        sums = dict(reversed(line.split('  ', 1)) for line in (HERE / 'SHA256SUMS').read_text().splitlines())
        for p in self.files:
            relative = 'study-records/' + p.name
            self.assertEqual(manifest.get(relative), sha(p.read_bytes()))
            self.assertEqual(sums.get(relative), sha(p.read_bytes()))


if __name__ == '__main__':
    unittest.main()
