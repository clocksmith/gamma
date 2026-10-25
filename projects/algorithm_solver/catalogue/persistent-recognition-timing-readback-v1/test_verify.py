import copy,importlib.util,unittest
from pathlib import Path
SPEC=importlib.util.spec_from_file_location('independent_readback',Path(__file__).with_name('verify.py'));v=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(v)
def fixture():
    freeze={'policy':{'id':'c65-m12','min_cosine':.65,'min_margin':.12},'stable_ids':[str(i)for i in range(4081)],'query_selection':[{'query_id':f'q{i}','text_sha256':'a'*64}for i in range(4)],'exact_ids':['leetcode:802','leetcode:875','leetcode:2406']}
    response={'status':'abstain','reason':'empirical_confidence_threshold','clarification_questions':[]};wire=v.encoded(response);rows=[]
    for i in range(14):
        row={'candidate_executions':0,'recognition_qualified':False,'goal_1c_qualified':False,'clarification_questions':[],'response_sha256':v.sha(wire),'response_bytes':len(wire)}
        if i<8:row.update(mode='description',query_position=i%4,pass_index=i//4,query_id=f'q{i%4}',query_sha256='a'*64,population=4081,cold_process_first_query=i==0,status='abstain',reason='empirical_confidence_threshold',timing_seconds={'query_encoding':1,'full_population_ranking':1,'empirical_decision_and_metadata':1,'response_serialization':1,'end_to_end':5})
        else:row.update(mode='exact-id-artifact',pass_index=(i-8)//3,control_id=freeze['exact_ids'][(i-8)%3],status='artifact_returned',artifacts={lang:{'source_sha256':'b'*64,'receipt_sha256':'c'*64,'bytes':1}for lang in ('javascript','python')},timing_seconds={'exact_id_metadata':1,'materialize_javascript':1,'materialize_python':1,'response_serialization':1,'end_to_end':5})
        rows.append(row)
    counts={'abstain':8,'artifact_returned':6,'error':0}
    report={'freeze_sha256':'f'*64,'status':'completed','requests':rows,'status_counts':counts,'description_requests':8,'exact_id_requests':6,'initialization_seconds':{'model':1,'all_initialization':2},'first_query_plus_initialization_seconds':7,'second_pass_description_seconds':[5]*4,'wall_seconds':73,'module_start_to_report_seconds':74,'cpu_seconds':15,'candidate_executions':0,'confirmation_read':False,'query_vector_cache':False,'source_availability_ranking_filter':False,'recognition_qualified':False,'goal_1c_qualified':False,'source_bytes_published':False}
    supervisor={'freeze_sha256':'f'*64,'status':'completed','exit_code':0,'error_type':None,'wall_timeout':False,'termination_signals':[],'wall_seconds':75,'owned_group_cleanup':{'leader_reaped':True,'live_members':[],'inspection_unreadable_pids':[],'no_executing_group_members_observed':True,'process_group_id':123}}
    progress={'status':'completed','completed_requests':14,'status_counts':counts}
    return freeze,report,supervisor,rows,progress,'f'*64
class VerifyTests(unittest.TestCase):
    def test_valid_arithmetic_and_status(self):
        r=v.validate(*fixture());self.assertEqual(r['description_abstentions'],8);self.assertEqual(r['description_artifact_successes'],0);self.assertEqual(r['exact_id_artifact_successes'],6)
    def test_stage_sum_failure(self):
        x=fixture();x[3][0]['timing_seconds']['end_to_end']=2
        with self.assertRaisesRegex(ValueError,'stage sum'):v.validate(*x)
    def test_cold_arithmetic_failure(self):
        x=fixture();x[1]['first_query_plus_initialization_seconds']=99
        with self.assertRaisesRegex(ValueError,'cold arithmetic'):v.validate(*x)
    def test_missing_response_hash(self):
        x=fixture();x[3][0]['response_sha256']='bad'
        with self.assertRaisesRegex(ValueError,'response hash'):v.validate(*x)
    def test_wrong_abstention_hash(self):
        x=fixture();x[3][0]['response_sha256']='e'*64
        with self.assertRaisesRegex(ValueError,'abstention response hash'):v.validate(*x)
    def test_live_group_fails(self):
        x=fixture();x[2]['owned_group_cleanup']['live_members']=[124]
        with self.assertRaisesRegex(ValueError,'cleanup'):v.validate(*x)
    def test_raw_source_rejected(self):
        x=fixture();x[1]['source_utf8']='synthetic'
        with self.assertRaisesRegex(ValueError,'raw source'):v.validate(*x)
    def test_incremental_final_mismatch(self):
        x=list(fixture());x[3]=copy.deepcopy(x[3]);x[3][0]['response_bytes']+=1
        with self.assertRaisesRegex(ValueError,'incremental'):v.validate(*x)
    def test_population_and_order(self):
        x=fixture();x[3][1]['query_position']=2
        with self.assertRaisesRegex(ValueError,'description order'):v.validate(*x)
if __name__=='__main__':unittest.main()
