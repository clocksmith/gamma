import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import report


def arm(name,value):
    rows={str(i):{'encodable':True,'actions':value,'selections':value-1,'single_characters':20,
                 'qualified_source':True,'eligible':False,'arm_eligible':False,
                 'prefix_codes':0,'identifier_codes':0} for i in range(100)}
    return {'arm':name,'entries':256,'illegal_entry_sha256':[],
            'dictionary_bytes':800,'decoder_dependency_bytes':200,
            'fit':{'covered':300,'qualified':300},'per_problem':rows,
            'validation':{'covered':100,'qualified':100,'actions':{'total':100*value,'median':value,'p90':value},
                          'single_character_fraction':.2,'package_bytes':10000}}


class ReportTests(unittest.TestCase):
    def test_toy_packet_measure_and_independent_replay(self):
        texts={'0':'function solve(a,b){let q=a.length;return q+b.length}',
               '1':'function solve(c,d){let r=c.length;return r+d.length}'}
        nodes=report.codec.extract(texts)
        pools={kind:list({n['key'] for group in nodes.values() for n in group[family] if n['key']})
               for kind,family in (('P','prefix'),('I','identifier'))}
        c={'partition':{'dev_fit':[0],'dev_val':[1]},'decoder_bytes':{'literal':1,'typed':2},
           'source_qualification':{pid:{'passed':True,'source_sha256':report.run.analyze.sha(text.encode())}
                                   for pid,text in texts.items()}}
        with tempfile.TemporaryDirectory() as temp:
            for arm in report.run.ARMS:
                folder=Path(temp)/arm
                folder.mkdir()
                keys=report.codec.order([report.codec.literal(x) for x in report.codec.ALPHABET]+
                    [k for kind,values in pools.items() if kind in report.run.ARMS[arm] for k in values])
                report.run.analyze.write(folder/'dictionary.json',keys)
                result=report.run.measure(arm,texts,nodes,keys,pools,folder,c)
                report.replay(folder,result,c,pools)
                forged=copy.deepcopy(result)
                forged['entries']+=1
                with self.assertRaises(AssertionError):report.replay(folder,forged,c,pools)
                forged=copy.deepcopy(result)
                forged['decoder_dependency_bytes']+=1
                with self.assertRaises(AssertionError):report.replay(folder,forged,c,pools)
                forged=copy.deepcopy(result)
                forged['per_problem']['0']['eligible']=not forged['per_problem']['0']['eligible']
                with self.assertRaises(AssertionError):report.replay(folder,forged,c,pools)

    def test_conditional_overlapping_and_empty_subsets_keep_global_costs(self):
        candidates={name:arm(name,value) for name,value in (('union',90),('literal',100),('D11',110))}
        own=candidates['union']
        own['dictionary_bytes']=1000
        for pid in ('0','1','2','3'):
            own['per_problem'][pid]['eligible']=True
            own['per_problem'][pid]['arm_eligible']=pid!='3'
        for pid in ('0','1'):own['per_problem'][pid]['prefix_codes']=1
        for pid in ('0','2'):own['per_problem'][pid]['identifier_codes']=1
        result=report.conditional_subsets(own,candidates,[3,1,4,0,2])
        sets=result['subsets']
        self.assertEqual(sets['common_pool_eligible']['ids'],['0','1','2','3'])
        self.assertEqual(sets['arm_pool_eligible']['ids'],['0','1','2'])
        self.assertEqual(sets['P_used']['ids'],['0','1'])
        self.assertEqual(sets['I_used']['ids'],['0','2'])
        self.assertEqual(sets['either_used']['ids'],['0','1','2'])
        self.assertEqual(sets['both_used']['ids'],['0'])
        both=sets['both_used']
        self.assertEqual(both['candidate']['attributed_packet_bytes'],41+89)
        self.assertEqual(both['candidate']['full_dictionary_plus_subset_packets_bytes'],1000+41+89)
        self.assertEqual(both['paired_costs']['literal']['candidate_minus_reference']['actions'],-10)
        self.assertEqual(both['paired_costs']['literal']['candidate_minus_reference']['full_dictionary_plus_subset_packets_bytes'],190)
        self.assertAlmostEqual(both['candidate']['single_character_fraction'],20/89)
        self.assertFalse(result['promotion_allowed'])
        empty=report.conditional_subsets(candidates['literal'],candidates,[0,1])['subsets']['both_used']
        self.assertEqual(empty['ids'],[])
        self.assertEqual(empty['candidate']['attributed_packet_bytes'],0)
        self.assertEqual(empty['candidate']['global_dictionary_bytes'],800)
        self.assertEqual(empty['candidate']['full_dictionary_plus_subset_packets_bytes'],800)
        self.assertIsNone(empty['candidate']['single_character_fraction'])
        self.assertIsNone(empty['candidate']['actions_per_program'])
        self.assertIsNone(empty['paired_costs']['literal']['fraction_difference'])
        own['per_problem']['3']['encodable']=False
        incomplete=report.conditional_subsets(own,candidates,[0,1,2,3])['subsets']['common_pool_eligible']
        self.assertEqual(incomplete['candidate']['failed_ids'],['3'])
        self.assertIsNone(incomplete['candidate']['selections'])
        self.assertEqual(incomplete['paired_costs']['literal']['paired']['worse'],1)

    def test_incomplete_supervisor_produces_no_verdict_report(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            report.run.analyze.write(root/'contract.json',{})
            report.run.analyze.write(root/'supervisor-receipt.json',{'complete':False,'outer_timeout':True,'promotion_allowed':False})
            with patch.object(report,'HERE',root):
                result=report.main(root)
            self.assertFalse(result['verdict_available'])
            self.assertFalse(result['flat_M1_promotion_allowed'])
            self.assertIsNone(result['selected_structured_candidate'])
            self.assertTrue((root/'REPORT.md').exists())

    def test_strict_incremental_union_and_no_flat_promotion(self):
        result={'arms':[arm('literal',100),arm('prefix',97),arm('template',96),arm('union',94),arm('D11',101)]}
        c={'partition':{'dev_val':list(range(100))}}
        got=report.build(result,c)
        self.assertEqual(got['selected_structured_candidate'],'union')
        self.assertFalse(got['flat_M1_promotion_allowed'])
        self.assertTrue(got['predictions']['S4_union_fewer_actions_than_both_single_kinds']['correct'])
        self.assertFalse(got['predictions']['S5_union_does_not_pass_full_stacking_rule']['correct'])
        result['arms'][2]=arm('template',94)
        self.assertIsNone(report.build(result,c)['selected_structured_candidate'])

    def test_coverage_and_package_cannot_be_hidden_by_mean_gain(self):
        a,b=arm('union',90),arm('literal',100)
        a['validation']['package_bytes']=10501
        self.assertFalse(report.checks(a,b,range(100),True)['package'])
        a['validation']['covered']=99
        a['per_problem']['0']['encodable']=False
        self.assertFalse(report.checks(a,b,range(100),True)['coverage_and_qualification'])
        self.assertEqual(report.paired(a,b,range(100))['worse'],1)
        b['per_problem']['0']['encodable']=False
        self.assertEqual(report.paired(a,b,range(100))['same'],1)


if __name__=='__main__':unittest.main()
