"""Invented monotone cardinality costs and certificates only; no solver or DP."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import quantile_diagnostics as q
import proof


def fixture(mode='sloped',scale=None):
    values=[None]+([max(0,40-k) for k in range(1,97)] if mode=='sloped' else [0]*96 if mode=='flat' else [None]*96)
    g=-3 if mode=='sloped' else 0
    caps={str(p):list(values) for p in range(300)};unrestricted={p:g for p in caps}
    def assignment(row,counts):
        if row[0] is None:return {'feasible':False,'hall_subset':1,'demand':counts[0],'neighbors':0}
        labels=[label for label,count in enumerate(counts) for _ in range(count)]
        return {'feasible':True,'value':sum(cost*count for cost,count in zip(row,counts)),
                'assignment':labels,'row_potentials':[0]*300,'category_potentials':row}
    necessary=assignment([values[32],values[96],g],[150,135,15])
    cases=[assignment([values[a],values[64-a],values[96],g],[150,1,134,15]) for a in range(1,33)]
    n=necessary.get('value');finite=[r['value'] for r in cases if r['feasible']];exact=min(finite) if finite else None
    summary={'scale':[1,1] if scale is None else scale,'denominator':1,'unrestricted_path_numerator':300*g,'top_capacity_numerator':0,
             'unrestricted_numerator':300*g,'unrestricted_integer_lower_bound':300*g,
             'necessary_path_numerator':n,'necessary_integer_lower_bound':n,
             'joint_path_numerator':exact,'joint_numerator':exact,'joint_integer_lower_bound':exact,
             'joint_path_increase':None if exact is None else exact-300*g,
             'quantiles_feasible_in_relaxed_pool':exact is not None,
             'excludes_fixed300_joint_target':exact is None or exact>0,'feasible_median_cases':len(finite)}
    return {'caps':caps,'unrestricted':unrestricted,'assignments':{'necessary':necessary,'median_cases':cases}},summary


def files(root):
    lit=root/'lit';here=lit/'joint';run=root/'run';main=root/'main';lit.mkdir();here.mkdir()
    source_hash='1'*64;q_hash='2'*64;parent_contract='3'*64
    parent={'complete':True,'validation_loaded':False,'contract_sha256':parent_contract,
            'arms':[{'cohort':name,'fit_source_sha256':source_hash,'certificate':{'q_sha256':q_hash,'independent_partition_and_integer_replay':True}} for name in ('R','naming')]}
    q.write(lit/'parent.json',parent)
    pins={'parent.json':q.sha(lit/'parent.json')}
    for i in range(120):
        path=lit/f'public-{i}.txt';path.write_text('invented public metadata');pins[path.name]=q.sha(path)
    contract={'active':True,'population':'fixed300_fit_only','scales':q.SCALES,'code_hashes':pins,'runtime_files':{},
              'parent_evidence':'parent.json','parent_contract_sha256':parent_contract,'denominator':1,
              'limits':{'production_seconds':1200,'report_seconds':1200,'cleanup_seconds':10},
              'private_files':{'NEVER_OPEN_SOURCE':source_hash,'NEVER_OPEN_Q':q_hash},
              'sources':{'R':'NEVER_OPEN_SOURCE','naming':'NEVER_OPEN_SOURCE'},'parent_q':{'R':'NEVER_OPEN_Q','naming':'NEVER_OPEN_Q'}}
    q.write(here/'contract.json',contract);digest=q.sha(here/'contract.json')
    arms=[];rawarms=[]
    for name in ('R','naming'):
        points=[];oldpoints=[]
        for i,scale in enumerate(q.SCALES):
            receipt,summary=fixture('sloped',scale);path=run/name/f'point-{i}.json';q.write(path,receipt)
            oldpoints.append({**summary,'proof_sha256':q.sha(path),'seconds':1})
            points.append({**summary,'proof_sha256':q.sha(path),'production_seconds':1,'replay_seconds':1})
        arm={'cohort':name,'complete':True,'validation_loaded':False,'fit_problems':300,'independent_cardinality_assignment_and_pool_replay':True,
             'source_sha256':source_hash,'parent_q_sha256':q_hash,'points':points}
        rawarm={'cohort':name,'complete':True,'validation_loaded':False,'source_sha256':source_hash,'parent_q_sha256':q_hash,'points':oldpoints}
        arms.append(arm);rawarms.append(rawarm);q.write(main/f'{name}.json',arm);q.write(run/name/'results.json',rawarm)
    raw={'complete':True,'validation_loaded':False,'contract_sha256':digest,'seconds':8,'arms':rawarms};q.write(run/'results.json',raw)
    report={'schema':'gamma.joint-quantile-fraction.report.v1','complete':True,'population':'fixed300_fit_only','validation_loaded':False,
            'contract_sha256':digest,'private_results_sha256':q.sha(run/'results.json'),'production_seconds':8,'replay_seconds':9,'arms':arms,'predictions':{'P1':True}}
    q.write(main/'results.json',report)
    for folder,phase in ((run,'production'),(main,'report')):
        q.write(folder/'supervisor.json',{'complete':True,'phase':phase,'contract_sha256':digest,'elapsed':10,'cleanup_seconds':.1,'returncodes':[0,0]})
    return lit,here,run,main,digest


class DiagnosticsTests(unittest.TestCase):
    def test_unique_argmin_tightness_and_exact_path_differences(self):
        receipt,summary=fixture()
        with patch.object(proof,'assignment_proof',side_effect=AssertionError('No optimization')),patch.object(proof,'tree_caps',side_effect=AssertionError('No DP')):
            got=q.diagnose(receipt,summary)
        self.assertEqual(got['all_minimizing_a'],[32]);self.assertEqual(got['selected_a'],32)
        self.assertEqual(got['tight_capped_programs'],151)
        self.assertEqual([r['tight_programs'] for r in got['classes']],[150,1,0,None])
        self.assertEqual(got['classes'][2]['minimum_edges_histogram'],{'40':134})
        self.assertEqual(got['exact_minus_necessary_path_numerator'],8)
        self.assertEqual(got['necessary_minus_unrestricted_path_numerator'],2055)

    def test_all_minimizers_plateaus_and_infeasible_family(self):
        receipt,summary=fixture('flat');got=q.diagnose(receipt,summary)
        self.assertEqual(got['all_minimizing_a'],list(range(1,33)));self.assertEqual(got['selected_a'],1)
        self.assertEqual(got['tight_capped_programs'],150)
        self.assertEqual(got['classes'][1]['selection_cap'],63)
        self.assertEqual(got['classes'][1]['minimum_edges_histogram'],{'1':1})
        self.assertEqual(q.minimum_edges([None,None,7,7]+[7]*93,2),(2,True))
        self.assertEqual(q.minimum_edges([None,None,7,7]+[7]*93,3),(2,False))
        receipt,summary=fixture('infeasible');got=q.diagnose(receipt,summary)
        self.assertFalse(got['quantile_family_feasible']);self.assertEqual(got['all_minimizing_a'],[])
        self.assertIsNone(got['selected_a']);self.assertIsNone(got['tight_capped_programs']);self.assertEqual(got['classes'],[])

    def test_corrupted_costs_potentials_assignments_and_summary_rejected(self):
        receipt,summary=fixture()
        for mutate in (
            lambda r,s:r['caps']['0'].__setitem__(33,99),
            lambda r,s:r['caps']['0'].__setitem__(0,0),
            lambda r,s:r['assignments']['median_cases'][31]['row_potentials'].__setitem__(0,1),
            lambda r,s:r['assignments']['median_cases'][31]['assignment'].__setitem__(0,3),
            lambda r,s:s.__setitem__('joint_path_numerator',s['joint_path_numerator']+1),
        ):
            r,s=copy.deepcopy(receipt),copy.deepcopy(summary);mutate(r,s)
            with self.assertRaises(AssertionError):q.diagnose(r,s)
        r,s=fixture('infeasible');r['assignments']['median_cases'][0]['neighbors']=150
        with self.assertRaises(AssertionError):q.diagnose(r,s)

    def test_full_receipt_provenance_hashes_and_failure_withdrawal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);lit,here,run,main,digest=files(root);output=root/'aux';report_hash=q.sha(main/'results.json')
            with patch.object(q,'LIT',lit),patch.object(q,'HERE',here),patch.object(q,'CONTRACT_SHA256',digest),patch.object(proof,'assignment_proof',side_effect=AssertionError('No solver')),patch.object(proof,'tree_caps',side_effect=AssertionError('No DP')):
                result=q.publish(run,main,report_hash,output)
                self.assertTrue(result['complete']);self.assertFalse(result['source_or_q_loaded'])
                self.assertEqual(len(result['arms']),2);self.assertTrue(all(len(a['points'])==6 for a in result['arms']))
                public=json.dumps(result)
                for private_key in ('"row_potentials":','"category_potentials":','"assignment":','"caps":','"unrestricted":'):
                    self.assertNotIn(private_key,public)
                with self.assertRaises(AssertionError):q.replay(run,main,'0'*64)
                path=run/'R/point-0.json';old=path.read_bytes();receipt=q.read(path);receipt['caps']['0'][32]+=1;q.write(path,receipt)
                with self.assertRaises(AssertionError):q.publish(run,main,report_hash,output)
                self.assertFalse(q.read(output/'results.json')['complete']);self.assertIn('No accepted diagnostics',(output/'REPORT.md').read_text())
                path.write_bytes(old)
                q.write(main/'failure.json',{'complete':False})
                with patch.object(q,'diagnose',side_effect=AssertionError('Must reject before any point diagnostics')):
                    with self.assertRaises(AssertionError):q.replay(run,main,report_hash)


if __name__=='__main__':unittest.main()
