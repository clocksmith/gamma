import copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
HERE=Path(__file__).parent
SPEC=importlib.util.spec_from_file_location('enriched102_test',HERE/'run.py');r=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(r)

def row(i,text,known=False):return {'problem_id':f'leetcode:{i}','text':text,'document_sha256':hashlib.sha256(text.encode()).hexdigest(),'authority':{'knowledge_class':'reviewed-normative-contract'if known else'title-only'}}
def pair():
    old={'stable_ids':[f'leetcode:{i}'for i in range(1,4082)],'documents':[row(i,f'synthetic title{i}',i<=54)for i in range(1,4082)]};new=copy.deepcopy(old)
    for i in range(54,102):new['documents'][i]=row(i+1,f'synthetic new contract{i+1}',True)
    return old,new
class Cache:
    @staticmethod
    def validate_array(a,n,np):
        if a.shape!=(n,1024)or a.dtype!=np.float32 or not np.allclose(np.linalg.norm(a,axis=1),1):raise ValueError('synthetic norm/shape')
class Encoder:
    def __init__(self,truncated=False):self.calls=[];self.truncated=truncated
    def encode(self,texts,query):
        self.calls.append((list(texts),query));self.last_request_info={'query':query,'rows':len(texts),'truncated':[self.truncated]*len(texts)}
        a=np.zeros((len(texts),1024),dtype=np.float32);a[:,0]=1;return a

def delta_fixture():
    old,new=pair();rows=new['documents'][54:102]
    f={'encoder_cache_identity':{'synthetic':'pinned'},'new_documents':{'sha256':'a'*64},'delta_batches':[]}
    for start in range(0,48,4):
        batch=rows[start:start+4];f['delta_batches'].append({'start':start,'ids':[x['problem_id']for x in batch],'binding_sha256':r.batch_binding(f['encoder_cache_identity'],'a'*64,batch)})
    return rows,f

class Tests(unittest.TestCase):
    def test_exact48_alignment_old54_unchanged(self):self.assertEqual(r.alignment(*pair()),list(range(54,102)))
    def test_old54_change_rejected(self):
        old,new=pair();new['documents'][0]=row(1,'changed original authority',True)
        with self.assertRaisesRegex(ValueError,'newly authoritative'):r.alignment(old,new)
    def test_order_population_tamper(self):
        old,new=pair();new['stable_ids']=new['stable_ids'][::-1]
        with self.assertRaises(ValueError):r.alignment(old,new)
    def test_text_hash_tamper(self):
        old,new=pair();new['documents'][100]['text']='tampered'
        with self.assertRaisesRegex(ValueError,'SHA'):r.alignment(old,new)
    def test_only48_doc_encodes_and_incremental_cache(self):
        rows,f=delta_fixture();encoder=Encoder()
        with tempfile.TemporaryDirectory()as d:
            array,receipts=r.encode_delta(encoder,rows,f,Path(d)/'cache',np,Cache())
            self.assertEqual(array.shape,(48,1024));self.assertEqual(len(receipts),12)
            self.assertEqual(len(list((Path(d)/'cache').glob('*.npy'))),12)
            self.assertEqual(json.loads((Path(d)/'progress.json').read_text())['completed_documents'],48)
        self.assertEqual(len(encoder.calls),12);self.assertEqual(sum(len(c[0])for c in encoder.calls),48)
        self.assertTrue(all(c[1]is False for c in encoder.calls))
    def test_truncated_doc_blocks_before_cache_write(self):
        rows,f=delta_fixture();encoder=Encoder(True)
        with tempfile.TemporaryDirectory()as d:
            with self.assertRaisesRegex(ValueError,'truncated'):r.encode_delta(encoder,rows,f,Path(d)/'cache',np,Cache())
            self.assertEqual(list((Path(d)/'cache').glob('*.npy')),[])
    def test_batch_binding_tamper_before_encode(self):
        rows,f=delta_fixture();f['delta_batches'][0]['binding_sha256']='bad';encoder=Encoder()
        with tempfile.TemporaryDirectory()as d:
            with self.assertRaisesRegex(ValueError,'batch drift'):r.encode_delta(encoder,rows,f,Path(d)/'cache',np,Cache())
        self.assertEqual(encoder.calls,[])
    def test_old_vectors_preserved_exactly(self):
        old=np.zeros((4081,1024),dtype=np.float32);old[:,0]=1
        delta=np.zeros((48,1024),dtype=np.float32);delta[:,1]=1
        new=r.install_delta(old,list(range(54,102)),delta,np)
        self.assertTrue(np.array_equal(new[:54],old[:54]));self.assertTrue(np.array_equal(new[102:],old[102:]))
        self.assertTrue(np.array_equal(old[:,0],np.ones(4081)))
        self.assertTrue(np.array_equal(new[54:102],delta))
    def test_gate_denial_before_any_document_payload(self):
        events=[];gate={'path':'gate','sha256':'g'}
        plans={'oldplan':{'boundary_gate':gate,'authorities':[{'problem_id':f'leetcode:{i}'}for i in range(54)]},'newplan':{'boundary_gate':gate,'authorities':[{'problem_id':f'leetcode:{i}'}for i in range(102)]},'gate':{'artifact_paths':{},'trusted_hashes':{}}}
        def read(spec):events.append(spec['path']);return plans[spec['path']]
        f={k:{'path':p}for k,p in [('old_document_plan','oldplan'),('new_document_plan','newplan'),('old_documents','olddocs'),('new_documents','newdocs')]}
        with patch.object(r,'pinned',side_effect=read),patch('projects.algorithm_solver.catalogue.boundary_policy.authorize_before_open',side_effect=PermissionError):
            with self.assertRaises(PermissionError):r.load_document_pair(f)
        self.assertNotIn('olddocs',events);self.assertNotIn('newdocs',events)
    def setup_comparison(self):
        from projects.algorithm_solver.catalogue.empirical_recognition import decide,score_decisions
        class Service:
            def __init__(self,available):self.available=available
            def request(self,pid,language=None,include_source=False):
                assert include_source is False
                if not self.available:return {'status':'abstain'}
                return {'status':'matched','consumer_selection':{'status':'selected','problem_id':pid,'language':language}}
        v8,v16=Service(False),Service(True)
        queries=[{'query_id':'synthetic','text':'owned fixture','kind':'positive','expected_id':'b'}]
        policies=[{'id':f'p{i}','min_cosine':.5,'min_margin':.1}for i in range(20)]
        rank54=[[('b',.9),('c',.1)]];rank102=[[('c',.9),('b',.1)]]
        history={p['id']:{'policy':p,'decisions':[decide(rank54[0],p,v8)],'metrics':score_decisions(queries,[decide(rank54[0],p,v8)])}for p in policies}
        return queries,rank54,rank102,policies,v8,v16,[False],history
    def test_service_effect_separated_from_document_effect(self):
        result,selected=r.compare(*self.setup_comparison());one=result[0]
        self.assertEqual(one['service_only_delta_v16_minus_v8']['correct_accepts'],1)
        self.assertEqual(one['document_only_delta_102_minus_54_at_v16']['correct_accepts'],-1)
        self.assertEqual(one['document_only_delta_102_minus_54_at_v16']['wrong_positive_accepts'],1)
        self.assertEqual(one['historical54_v8']['abstentions'],1)
        self.assertEqual(set(selected),{'historical54_v8','baseline54_v16','expanded102_v16'})
    def test_historical_reproduction_required(self):
        args=list(self.setup_comparison());args[-1]['p0']['decisions'][0]={'status':'accepted','problem_id':'b'}
        with self.assertRaisesRegex(ValueError,'reproduction'):r.compare(*args)
    def test_policy_family_count_fixed(self):
        args=list(self.setup_comparison());args[3]=args[3][:-1]
        with self.assertRaisesRegex(ValueError,'20policies'):r.compare(*args)

if __name__=='__main__':unittest.main()
