"""Validate the cohort's study.record.v1 records against the problem_catalogue schema and check every hash binding."""
import hashlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

HERE = Path(__file__).parent
GAMMA = HERE.parents[4]
SCHEMA = json.loads((GAMMA / 'projects/problem_catalogue/schema.v1.json').read_text())
RECORDS = sorted((HERE / 'study-records').glob('*.json'))
ALLOWED_EDGES = {('approach', 'contract'), ('approach', 'artifact'), ('artifact', 'contract')}
VARIANTS = [row['uid'] for row in json.loads((HERE / 'contracts.json').read_text())['problems']]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def walk(value):
    if isinstance(value, dict):
        yield value
        for item in value.values(): yield from walk(item)
    elif isinstance(value, list):
        for item in value: yield from walk(item)


class StudyRecords(unittest.TestCase):
    def test_schema_valid(self):
        validator = Draft202012Validator(SCHEMA)
        for path in RECORDS:
            errors = sorted(validator.iter_errors(json.loads(path.read_text())), key=lambda e: list(e.path))
            self.assertFalse(errors, f'{path.name}: {errors[0].message[:300] if errors else ""}')

    def test_names_and_counts(self):
        kinds = {}
        for path in RECORDS:
            record = json.loads(path.read_text())
            self.assertEqual(path.name, f"{record['kind']}--{record['id'].replace(':', '_')}.json")
            self.assertEqual((record['schema'], record['version']), ('study.record.v1', 1))
            kinds[record['kind']] = kinds.get(record['kind'], 0) + 1
        n = len(VARIANTS)
        self.assertEqual(kinds, {'contract': n, 'approach': n, 'artifact': 3 * n})

    def test_hash_bindings_and_acyclic_order(self):
        by_path = {str(p.relative_to(GAMMA)): json.loads(p.read_text()) for p in RECORDS}
        for path, record in by_path.items():
            for node in walk(record):
                if {'repository', 'path', 'sha256', 'selector'} <= node.keys():  # SourcePointer
                    self.assertEqual(sha(GAMMA / node['path']), node['sha256'], f'{path} -> {node["path"]}')
                elif {'kind', 'id', 'version', 'path', 'sha256'} == node.keys():  # Ref
                    self.assertEqual(sha(GAMMA / node['path']), node['sha256'], f'{path} -> {node["id"]}')
                    self.assertEqual(by_path[node['path']]['id'], node['id'])
                    # only approach -> contract/artifact and artifact -> contract edges: acyclic by construction
                    self.assertIn((record['kind'], by_path[node['path']]['kind']), ALLOWED_EDGES)
                elif {'path', 'sha256', 'bytes', 'mediaType'} == node.keys():  # FileRef
                    self.assertEqual(sha(GAMMA / node['path']), node['sha256'])
                    self.assertEqual((GAMMA / node['path']).stat().st_size, node['bytes'])

    def test_no_qualification_or_evidence_records(self):
        for path in RECORDS:
            self.assertIn(json.loads(path.read_text())['kind'], ('contract', 'approach', 'artifact'))

    def test_inferred_scope_and_coding_stages(self):
        for path in RECORDS:
            record = json.loads(path.read_text())
            if record['kind'] == 'contract':
                self.assertEqual(record['contentScope'], 'authored')
                self.assertEqual({i['language'] for i in record['interfaces']}, {'python', 'javascript'})
            if record['kind'] == 'approach':
                self.assertEqual([s['type'] for s in record['stages']], ['reasoning', 'coding', 'validation'])
                self.assertEqual(len(record['stages'][1]['artifacts']), 2)
                self.assertEqual(record['sequenceStatus'], 'draft')


if __name__ == '__main__': unittest.main()
