from pathlib import Path
import hashlib
import json
import unittest
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


class StudyRecords(unittest.TestCase):
    def test_shapes_hashes_references_and_provenance(self):
        schema = json.loads((ROOT/'projects/problem_catalogue/schema.v1.json').read_text())
        paths = list((HERE/'study-records').glob('*.json'))
        self.assertEqual(len(paths),225)
        seen = set()
        def walk(value):
            if isinstance(value,dict):
                if set(value)=={'kind','id','version','path','sha256'}:
                    raw=(ROOT/value['path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),value['sha256']);target=json.loads(raw);self.assertEqual((target['kind'],target['id'],target['version']),(value['kind'],value['id'],value['version']))
                if set(value)=={'repository','revision','path','sha256','selector'}:
                    raw=(ROOT/value['path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),value['sha256'])
                    if value['selector']:
                        data=json.loads(raw)
                        for part in value['selector'].lstrip('/').split('/'):
                            part=part.replace('~1','/').replace('~0','~');data=data[int(part)] if isinstance(data,list) else data[part]
                for child in value.values():walk(child)
            elif isinstance(value,list):
                for child in value:walk(child)
        for path in paths:
            value=json.loads(path.read_text());key=(value['kind'],value['id']);self.assertNotIn(key,seen);seen.add(key)
            self.assertNotIn(value['kind'],('evidence','admission'))
            definition=value['kind'].title().replace('-','');Draft202012Validator({**schema,'oneOf':[{'$ref':'#/$defs/'+definition}]}).validate(value);walk(value)


if __name__ == '__main__':
    unittest.main()
