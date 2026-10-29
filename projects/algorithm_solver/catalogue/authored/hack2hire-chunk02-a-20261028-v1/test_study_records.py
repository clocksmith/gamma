"""Validate this cohort's study.record.v1 records against the problem_catalogue schema (read-only use)."""
import hashlib
import json
from pathlib import Path
import unittest

import jsonschema

HERE = Path(__file__).parent
GAMMA = HERE.parents[4]
SCHEMA = json.loads((GAMMA / 'projects/problem_catalogue/schema.v1.json').read_text())
RECORDS = sorted((HERE / 'study-records').glob('*.json'))
CONTRACTS = json.loads((HERE / 'contracts.json').read_text())['problems']


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def walk(value):
    if isinstance(value, dict):
        yield value
        for v in value.values(): yield from walk(v)
    elif isinstance(value, list):
        for v in value: yield from walk(v)


class StudyRecords(unittest.TestCase):
    def test_schema(self):
        validator = jsonschema.Draft202012Validator(SCHEMA)
        self.assertEqual(len(RECORDS), len(CONTRACTS) * 5)  # contract, 2 implementations, study-native, approach
        for path in RECORDS:
            record = json.loads(path.read_text())
            errors = sorted(validator.iter_errors(record), key=str)
            self.assertEqual(errors, [], f'{path.name}: {errors[:1]}')
            self.assertEqual(path.name, f"{record['kind']}--{record['id'].replace(':', '_')}.json")

    def test_refs_files_and_provenance(self):
        ids = {}
        for path in RECORDS:
            record = json.loads(path.read_text())
            ids[record['id']] = record['kind']
            for node in walk(record):
                if set(node) == {'kind', 'id', 'version', 'path', 'sha256'}:  # Ref
                    self.assertEqual(sha(GAMMA / node['path']), node['sha256'], f'{path.name} -> {node["id"]}')
                    self.assertEqual(json.loads((GAMMA / node['path']).read_text())['id'], node['id'])
                elif {'repository', 'revision', 'path', 'sha256', 'selector'} <= set(node):  # SourcePointer
                    self.assertEqual(sha(GAMMA / node['path']), node['sha256'], f'{path.name} provenance {node["path"]}')
                elif set(node) == {'path', 'sha256', 'bytes', 'mediaType'}:  # FileRef
                    target = GAMMA / node['path']
                    self.assertEqual((sha(target), target.stat().st_size), (node['sha256'], node['bytes']))
        for c in CONTRACTS:
            pid, vid = 'hack2hire:' + c['group_post_id'], c['variant_id']
            self.assertEqual(ids[f'contract:{pid}:{vid}:authored-v1'], 'contract')
            self.assertEqual(ids[f'approach:{pid}:{vid}:v1'], 'approach')
            for lang in ('python', 'javascript'): self.assertEqual(ids[f'artifact:{pid}:{vid}:{lang}:v1'], 'artifact')

    def test_scope_and_status(self):
        for path in RECORDS:
            record = json.loads(path.read_text())
            if record['kind'] == 'contract':
                self.assertEqual(record['contentScope'], 'authored')
                self.assertTrue(record['assumptions']['value'])
            if record['kind'] == 'approach':
                self.assertEqual(record['sequenceStatus'], 'draft')
                self.assertEqual([s['type'] for s in record['stages']], ['reasoning', 'coding', 'validation'])
                self.assertEqual(len(record['stages'][1]['artifacts']), 2)


if __name__ == '__main__': unittest.main()
