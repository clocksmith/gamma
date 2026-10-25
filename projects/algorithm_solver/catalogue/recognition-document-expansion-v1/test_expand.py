import importlib.util,unittest
from pathlib import Path
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('normative_expansion',Path(__file__).with_name('expand.py'));e=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(e)
class ExpansionTests(unittest.TestCase):
    def baseline(self):return {'authorities':[{'problem_id':f'leetcode:{i}','problem_contract_sha256':'a'*64}for i in range(1,55)]}
    def test_complete_adoption_union(self):
        s=[{'new_problem_ids':[f'leetcode:{i}'for i in range(start,start+8)]}for start in range(55,103,8)]
        self.assertEqual(len(e.identity_union(self.baseline(),s,102)),102)
    def test_overlap_unknown_or_missing_metadata_rejected(self):
        for additions in (None,[],['leetcode:1']*8,[f'leetcode:{i}'for i in range(1,9)]):
            with self.assertRaises(ValueError):e.identity_union(self.baseline(),[{'new_problem_ids':additions}],62)
    def test_gate_denial_precedes_combined_catalogue(self):
        events=[];old=dict(self.baseline(),boundary_gate={'path':'gate'})
        service={'source_access':{'boundary_gate':{'path':'gate'}},'catalogue':{'path':'catalogue'}}
        def reader(spec):
            name=spec['path'];events.append(('read',name))
            return {'old':old,'service':service,'gate':{'artifact_paths':{},'trusted_hashes':{}}}[name]
        def authorize(pid,*args,**kw):events.append(('gate',pid));raise PermissionError
        with self.assertRaises(PermissionError):e.assemble({'baseline_plan':{'path':'old'},'adoption_statuses':[],'expected_normative':54,'service':{'path':'service'}},reader=reader,authorize=authorize)
        self.assertNotIn(('read','catalogue'),events)
    def test_every_authority_gated_before_combined_read(self):
        events=[];old=dict(self.baseline(),boundary_gate={'path':'gate'})
        service={'source_access':{'boundary_gate':{'path':'gate'}},'catalogue':{'path':'catalogue'},'universe':{'path':'universe'},'verified_receipts':{'path':'receipts'}}
        def reader(spec):
            name=spec['path'];events.append(('read',name))
            if name=='catalogue':
                self.assertEqual(sum(x[0]=='gate'for x in events),54);raise RuntimeError('stop before payload')
            return {'old':old,'service':service,'gate':{'artifact_paths':{},'trusted_hashes':{}}}[name]
        with self.assertRaisesRegex(RuntimeError,'stop'):e.assemble({'baseline_plan':{'path':'old'},'adoption_statuses':[],'expected_normative':54,'service':{'path':'service'}},reader=reader,authorize=lambda pid,*a,**k:events.append(('gate',pid)))
    def documents(self):
        rows=[{'problem_id':str(i),'text':'synthetic '+str(i),'authority':{'knowledge_class':'normative'if i<54 else'title-only'}}for i in range(4081)]
        return {'population':4081,'stable_ids':[str(i)for i in range(4081)],'documents':rows,'enriched':54}
    def test_all4081_retained_and_only_new_authorities_change(self):
        import copy
        old=self.documents();new=copy.deepcopy(old);ids={str(i)for i in range(62)}
        for i in range(54,62):new['documents'][i]['text']+=' new permitted semantics';new['documents'][i]['authority']['knowledge_class']='normative'
        new['enriched']=62
        self.assertEqual(len(e.check_expansion(old,new,ids)),8)
    def test_old_semantics_and_unknown_titles_cannot_change(self):
        import copy
        for index in (0,4000):
            old=self.documents();new=copy.deepcopy(old);new['documents'][index]['text']='changed'
            with self.assertRaises(ValueError):e.check_expansion(old,new,{str(i)for i in range(54)})
    def test_population_filter_rejected(self):
        old=self.documents();new=self.documents();new['stable_ids']=new['stable_ids'][:-1]
        with self.assertRaises(ValueError):e.check_expansion(old,new,set())
if __name__=='__main__':unittest.main()
