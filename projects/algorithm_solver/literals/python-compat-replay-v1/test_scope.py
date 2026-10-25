import importlib.util,json,tempfile,unittest
from pathlib import Path
P=Path(__file__).with_name('qualify.py');s=importlib.util.spec_from_file_location('compat_scope_test',P);q=importlib.util.module_from_spec(s);s.loader.exec_module(q)

class ScopeTests(unittest.TestCase):
    def fixture(self,root):
        folder=root/'sources';(folder/'python').mkdir(parents=True)
        raw=b'def solve(x):\n return x\n';sem=q.encoded({'problem_id':6,'language':'python','entry_point':'solve'})
        (folder/'python/0006.py').write_bytes(raw);(folder/'python/0006.semantics.json').write_bytes(sem)
        m={'schema':'gamma.python.reference-compatibility.sources.v1','partition':'dev_fit','ids':[6],'sources':[{'id':6,'path':'python/0006.py','sha256':q.sha(raw),'bytes':len(raw),'entry_point':'solve','semantics_path':'python/0006.semantics.json','semantics_sha256':q.sha(sem),'reference_source_sha256':'0'*64}],'candidate_executions':0,'qualified':0,'protected_access':False,'evidence_class':'extra-contract-reference-compatibility-probe','normative_domain_resolved':False}
        return folder,m
    def test_explicit_probe_freeze(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder,m=self.fixture(root);q.write(folder/'manifest.json',m)
            c=q.freeze(root/'freeze',folder);self.assertFalse(c['normative_domain_resolved']);self.assertFalse(c['dictionary_fitting_allowed']);self.assertEqual(q.load_freeze(root/'freeze')[0],c)
    def test_no_normative_or_wrong_partition(self):
        for key,value in [('qualified',1),('normative_domain_resolved',True),('partition','dev_val'),('protected_access',True)]:
            with self.subTest(key=key),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);folder,m=self.fixture(root);m[key]=value;q.write(folder/'manifest.json',m)
                with self.assertRaises(ValueError):q.freeze(root/'freeze',folder)

if __name__=='__main__':unittest.main()
