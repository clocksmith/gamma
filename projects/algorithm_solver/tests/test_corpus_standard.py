import copy,hashlib,json,unittest
from pathlib import Path
from algsolve.corpus_standard import analyze,check_candidate,check_semantics
ROOT=Path(__file__).resolve().parents[1] / "contracts"
POLICY=json.loads((ROOT/'corpus_standard_v1.json').read_text())
class StandardChecks(unittest.TestCase):
    def run_check(self, source, language, policy=None, entry=None):
        policy=policy or POLICY['languages'][language]
        entry=entry or {'method':'findMin','params':['nums'],'internal':'findRotatedMinimum' if language=='javascript' else 'find_rotated_minimum'}
        initial=analyze(source,language,policy,entry)
        source=initial.get('formatted',source)
        inspected=analyze(source,language,policy,entry)
        mapping={'schema':'algsolve.reviewed-bindings.v1','reviewed_by':'explicit test fixture roles','source_sha256':hashlib.sha256(source.encode()).hexdigest(),'bindings':{k:v['role'] for k,v in inspected.get('bindings',{}).items()}}
        return analyze(source,language,policy,entry,mapping),source,mapping,entry,policy
    def base(self,lang):
        return ('function findRotatedMinimum(values) { return values[0]; }\nclass Solution { findMin(nums) { return findRotatedMinimum(nums); } }' if lang=='javascript' else 'def find_rotated_minimum(values: list[int]) -> int:\n    return values[0]\nclass Solution:\n    def findMin(self, nums: list[int]) -> int:\n        return find_rotated_minimum(nums)\n')
    def test_formatter_idempotence_and_public_signature(self):
        for lang in ['javascript','python']:
            result,source,mapping,entry,policy=self.run_check(self.base(lang),lang)
            self.assertEqual(result['errors'],[])
            self.assertEqual(analyze(source,lang,policy,entry)['formatted'],source)
            broken=source.replace('findMin','wrongName')
            self.assertTrue(analyze(broken,lang,policy,entry,mapping)['errors'])
    def test_missing_stale_ambiguous_mappings_fail(self):
        for lang in ['javascript','python']:
            result,source,mapping,entry,policy=self.run_check(self.base(lang),lang)
            bad=copy.deepcopy(mapping);bad['bindings']={}
            self.assertTrue(analyze(source,lang,policy,entry,bad)['errors'])
            bad=copy.deepcopy(mapping);bad['source_sha256']='0'*64
            self.assertIn('stale reviewed mapping',analyze(source,lang,policy,entry,bad)['errors'])
            self.assertIn('reviewed binding mapping required',check_candidate(source,lang,policy,entry,None,{})['errors'])
    def test_adapter_order_and_helper_signatures(self):
        for lang in ['javascript','python']:
            s=self.base(lang)
            s=s.replace('findRotatedMinimum(nums)','findRotatedMinimum([])').replace('find_rotated_minimum(nums)','find_rotated_minimum([])')
            self.assertTrue(self.run_check(s,lang)[0]['errors'])
            s=self.base(lang).replace('Minimum(values)','Minimum(targetValue)').replace('minimum(values:','minimum(target_value:')
            self.assertTrue(self.run_check(s,lang)[0]['errors'])
    def test_shadowing_and_captured_binding_resolution(self):
        for lang in ['javascript','python']:
            p=copy.deepcopy(POLICY['languages'][lang]);name='readValue' if lang=='javascript' else 'read_value'
            p['roles']['read_value']=name;p['helpers'][name]={'params':[]}
            if lang=='javascript':
                source='function findRotatedMinimum(values) { function readValue() { return values[0]; } return readValue(); } class Solution { findMin(nums) { return findRotatedMinimum(nums); } }'
            else:
                source='def find_rotated_minimum(values: list[int]) -> int:\n    def read_value() -> int:\n        return values[0]\n    return read_value()\nclass Solution:\n    def findMin(self, nums: list[int]) -> int:\n        return find_rotated_minimum(nums)\n'
            result,*_=self.run_check(source,lang,p)
            self.assertEqual(result['errors'],[])
            self.assertTrue(any(x['binding'].endswith(':values') for x in result['captures']))
            if lang=='javascript':source=source.replace('readValue() { return','readValue(values) { return')
            else:source=source.replace('read_value() ->','read_value(values: list[int]) ->')
            result,*_=self.run_check(source,lang,p)
            self.assertTrue(any('shadowing' in e for e in result['errors']))
    def test_properties_not_variable_bindings(self):
        for lang in ['javascript','python']:
            source=self.base(lang).replace('values[0]','values.length' if lang=='javascript' else 'values.real')
            result,formatted,*_=self.run_check(source,lang)
            self.assertEqual(result['errors'],[])
            self.assertIn('values.length' if lang=='javascript' else 'values.real',formatted)
            self.assertFalse(any(v['name'] in ['length','real'] for v in result['bindings'].values()))
    def test_unknown_role_and_incomplete_semantics_rejected(self):
        for lang in ['javascript','python']:
            self.assertTrue(self.run_check(self.base(lang).replace('values','mystery'),lang)[0]['errors'])
        self.assertTrue(check_semantics({'schema':'algsolve.corpus-semantics.v1'}))
    def test_noncanonical_format_rejected(self):
        for lang in ['javascript','python']:
            _,source,mapping,entry,policy=self.run_check(self.base(lang),lang)
            changed=source+'\n';mapping['source_sha256']=hashlib.sha256(changed.encode()).hexdigest()
            self.assertIn('noncanonical formatting',analyze(changed,lang,policy,entry,mapping)['errors'])
    def test_missing_internal_and_callable_reassignment_rejected(self):
        for lang in ['javascript', 'python']:
            missing = ('class Solution { findMin(nums) { return findRotatedMinimum(nums); } }'
                       if lang == 'javascript' else 'class Solution:\n    def findMin(self, nums: list[int]) -> int:\n        return find_rotated_minimum(nums)\n')
            self.assertTrue(self.run_check(missing, lang)[0]['errors'])
            for name in ['Solution', 'findRotatedMinimum' if lang == 'javascript' else 'find_rotated_minimum']:
                self.assertTrue(self.run_check(self.base(lang) + '\n' + name + ' = 0' + (';' if lang == 'javascript' else '\n'), lang)[0]['errors'])
    def test_unsupported_callable_and_binding_constructs_rejected(self):
        for source in [self.base('javascript').replace('function ', 'async function ', 1),
                       'const findRotatedMinimum = (targetValue) => targetValue[0]; class Solution { findMin(nums) { return findRotatedMinimum(nums); } }']:
            self.assertTrue(self.run_check(source, 'javascript')[0]['errors'])
        for suffix in ['\nimport math as secret_alias\n', '\ntry:\n    pass\nexcept ValueError as mystery:\n    pass\n', '\nreturn 0\n']:
            self.assertTrue(self.run_check(self.base('python') + suffix, 'python')[0]['errors'])
    def test_conditional_declarations_and_adapter_mutation_rejected(self):
        self.assertTrue(self.run_check(self.base('javascript').replace('findMin(nums) {', 'set findMin(nums) {'), 'javascript')[0]['errors'])
        for lang in ['javascript','python']:
            suffix = '\nSolution.prototype.findMin = 0;' if lang == 'javascript' else '\nSolution.findMin = 0\n'
            self.assertTrue(self.run_check(self.base(lang) + suffix, lang)[0]['errors'])
        source = 'if False:\n' + '\n'.join('    '+line for line in self.base('python').splitlines()) + '\n'
        self.assertTrue(self.run_check(source, 'python')[0]['errors'])
    def test_unregistered_object_methods_and_spread_calls_rejected(self):
        source = self.base('javascript').replace('return values[0];', 'const resultValues = { mystery(value) { return value; } }; return values[0];')
        self.assertTrue(self.run_check(source, 'javascript')[0]['errors'])
        for lang in ['javascript', 'python']:
            source = self.base(lang).replace('return values[0];', 'return findRotatedMinimum(...values);').replace('return values[0]\n', 'return find_rotated_minimum(*values)\n')
            self.assertTrue(self.run_check(source, lang)[0]['errors'])
if __name__=='__main__':unittest.main()
