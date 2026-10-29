import hashlib
import json
from pathlib import Path
import unittest
import jsonschema
ROOT=Path(__file__).resolve().parent
GAMMA=ROOT.parents[4]
class StudyRecords(unittest.TestCase):
    def test_schema_and_reference_hashes(self):
        schema=json.loads((GAMMA/'projects/problem_catalogue/schema.v1.json').read_text());validator=jsonschema.Draft202012Validator(schema)
        for path in (ROOT/'study-records').glob('*.json'):
            record=json.loads(path.read_text());validator.validate(record)
            def visit(value):
                if isinstance(value,dict):
                    if set(('kind','id','version','path','sha256'))<=value.keys():
                        target=GAMMA/value['path'];self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(),value['sha256']);actual=json.loads(target.read_text());self.assertEqual((actual['kind'],actual['id'],actual['version']),(value['kind'],value['id'],value['version']))
                    if value.get('repository')=='gamma' and 'sha256' in value:self.assertEqual(hashlib.sha256((GAMMA/value['path']).read_bytes()).hexdigest(),value['sha256'])
                    for item in value.values():visit(item)
                elif isinstance(value,list):
                    for item in value:visit(item)
            visit(record)
    def test_no_admission_or_evidence_records(self):
        records=[json.loads(p.read_text()) for p in (ROOT/'study-records').glob('*.json')];self.assertTrue(records);self.assertFalse(any(r['kind'] in ('admission','evidence','problem') for r in records))
if __name__=='__main__':unittest.main()
