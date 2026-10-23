"""Reporting-only synthetic additions; frozen execution tests are untouched."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import backend
report = backend.module('fraction_primal_auxiliary_report', backend.HERE / 'report.py')

class ReportingAuxTests(unittest.TestCase):
    def synthetic_witness(self, selections, characters):
        stats=[{'distinct_program_support':owners,'maximum_fraction_of_containing_source':fraction,
                'selection_uses':0 if i==2 else 1}
               for i,(owners,fraction) in enumerate([(1,.9),(2,.8999),(1,1.0),(3,.95),(1,.2)])]
        return {'entry_statistics':stats,'entries':5,'one_owner_entries':3,
                'entries_covering_at_least_90_percent_of_a_source':3,
                'selections':backend.analyze.distribution(selections),
                'actions':backend.analyze.distribution([n+1 for n in selections]),
                'characters':characters,'character_fraction':characters/sum(selections),
                'objective':10*characters-sum(selections)}

    def test_entry_shares_keep_inherited_threshold_and_all_entry_denominator(self):
        summary=report.witness_summary(self.synthetic_witness([10,20,30],12))
        self.assertEqual(summary['one_owner_entries'],3);self.assertEqual(summary['one_owner_entry_share'],.6)
        self.assertEqual(summary['near_whole_entries'],3);self.assertEqual(summary['near_whole_entry_share'],.6)
        self.assertEqual(summary['one_owner_and_near_whole_entries'],2)
        self.assertEqual(summary['one_owner_and_near_whole_entry_share'],.4)
        self.assertEqual(summary['near_whole_threshold'],.9)
        self.assertEqual(summary['N'],60);self.assertEqual(summary['actions'],63)
        self.assertEqual((summary['median_selections'],summary['p90_selections'],summary['p95_selections']),(20,30,30))

    def test_lower_fraction_and_F_can_coexist_with_higher_N(self):
        summaries=report.summarize_witnesses({'seed':self.synthetic_witness([10,20,30],12),
                                            'warm':self.synthetic_witness([12,24,36],10)})
        self.assertEqual(set(summaries),{'seed','warm'}) # No invented infeasible-cold costs.
        delta=summaries['warm']['relative_to_minimum_F_seed']
        self.assertEqual(delta['N_delta'],12);self.assertEqual(delta['actions_delta'],12)
        self.assertLess(delta['character_fraction_delta'],0);self.assertLess(delta['F_delta'],0)
        self.assertTrue(delta['lower_fraction_with_higher_N']);self.assertTrue(delta['lower_F_with_higher_N'])
        self.assertFalse(summaries['seed']['relative_to_minimum_F_seed']['lower_fraction_with_higher_N'])

    def test_summary_reports_actual_min_F_packets_not_shortest_N(self):
        texts={'toy':'abcdef'};vocab=['abcd','ef','ab','cd']
        with tempfile.TemporaryDirectory() as temporary:
            private=Path(temporary)/'witness'
            raw=backend.measure(texts,vocab,private,0)
            clean,_=report.packet_audit.witness(private,raw,texts,set(),{'pool':{'capacity':256},'decoder_dependency_bytes':0},-10)
            summary=report.witness_summary(clean)
            self.assertEqual(summary['N'],3);self.assertEqual(summary['F'],-3)
            self.assertEqual(len(backend.analyze.shortest_encode(texts['toy'],vocab)),2)
            self.assertEqual(summary['path_policy'],report.PATH_POLICY)

    def test_complete_synthetic_report_includes_seed_and_every_feasible_witness(self):
        frozen_tests=backend.module('fraction_primal_original_report_fixture',backend.HERE/'test_report.py')
        with tempfile.TemporaryDirectory() as temporary:
            here,lit,work,out,_=frozen_tests.ReportTests().fixture(Path(temporary))
            with patch.object(backend,'LIT',lit):result=report.build_report(out,work,here,lit)
            self.assertTrue(result['complete'])
            for arm in result['arms']:
                summaries=arm['witness_cost_and_entry_share_summary']
                self.assertEqual(set(summaries),set(arm['witnesses']))
                for name,row in summaries.items():
                    self.assertEqual(row['N'],arm['witnesses'][name]['selections']['total'])
                    self.assertEqual(row['actions'],row['N']+300)
                    self.assertEqual(row['p95_selections'],arm['witnesses'][name]['selections']['p95'])
            self.assertNotIn('function solve',json.dumps(result))
            report.write_report(result,here);markdown=(here/'README.md').read_text()
            for label in ('| Median N | p90 N | p95 N |','One-owner entries / share','Near-whole entries / share','minimum-F paths'):
                self.assertIn(label,markdown)
            failure={'complete':False,'status':'synthetic failure; no verdict'}
            report.write_report(failure,here)
            self.assertNotIn('| Cohort |',(here/'README.md').read_text())


if __name__ == '__main__':unittest.main()
