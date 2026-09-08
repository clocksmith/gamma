"""Reports retain unknown costs, populations and reviewed terminal evidence."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from projects.enwiki9.tools import enwiki9_evidence_matrix as evidence
from projects.enwiki9.tools import enwiki9_best_results as best
from projects.enwiki9.tools import record_driver_result as recorder


class TerminalReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)

    def receipt(self,name='candidate',**fields):
        p=self.root/(name+'.json')
        p.write_text(json.dumps(dict(program_id=name,data_size=250000,compressed_size=60000,
            roundtrip_ok=True,determinism={'single_host_byte_equal':True},**fields)))
        return p

    def test_unknown_program_cost_never_becomes_free(self):
        for fields in ({},{'program_size':None},{'program_size':False},{'program_size':-1},
                       {'program_size':10,'score_accounting_complete':False}):
            row=evidence.load_row(self.receipt(**fields))
            self.assertIsNone(row.score)
            self.assertEqual(evidence.top_rows([row],250000,'score',3),[])
            self.assertEqual(evidence.top_rows([row],250000,'archive',3),[row])
            self.assertEqual(row.archive_bpb,1.92)
        row=evidence.load_row(self.receipt(program_size=0))
        self.assertEqual(row.score,60000)  # Explicit legacy zero differs from missing.

    def test_population_and_arm_survive_display(self):
        rows=[evidence.load_row(self.receipt(name=n,data_sha256=n*64,arm='D')) for n in ('a','b')]
        with patch.object(evidence,'ROOT',self.root):rendered=best.render(rows,1)
        self.assertIn('Population `'+64*'a'+'`',rendered)
        self.assertIn('Population `'+64*'b'+'`',rendered)
        self.assertIn('`a:D`',rendered);self.assertIn('`b:D`',rendered)
        self.assertIn('unknown',rendered)

    def terminal(self):
        result=self.receipt(arm='K')
        index=self.root/'operations/provenance/terminal/index.json';index.parent.mkdir(parents=True)
        index.write_text(json.dumps(dict(schema='gamma.enwiki9.terminal-result-index.v1',
            arms=[dict(arm='K',result=dict(path=result.name))])))
        return index,result

    def test_terminal_uses_existing_read_only_validator(self):
        index,result=self.terminal();issues=[]
        with patch.object(evidence,'ROOT',self.root),patch.object(recorder,'ROOT',self.root),\
             patch.object(recorder,'record_terminal',return_value={'missing_rows':0}) as verify:
            self.assertEqual(evidence.reviewed_terminal_paths({index,result},issues),{result})
        verify.assert_called_once_with('candidate',index,check_only=True)
        self.assertEqual(issues,[])

    def test_untracked_or_unrecorded_or_invalid_terminal_is_disclosed(self):
        index,result=self.terminal()
        with patch.object(evidence,'ROOT',self.root),patch.object(recorder,'ROOT',self.root),\
             patch.object(recorder,'record_terminal') as verify:
            issues=[];self.assertEqual(evidence.reviewed_terminal_paths({index},issues),set())
            verify.assert_not_called();self.assertIn('not tracked',issues[0])
            verify.return_value={'missing_rows':1}
            issues=[];self.assertEqual(evidence.reviewed_terminal_paths({index,result},issues),set())
            self.assertIn('not recorded',issues[0])
            verify.side_effect=ValueError('replaced archive')
            issues=[];self.assertEqual(evidence.reviewed_terminal_paths({index,result},issues),set())
            self.assertIn('replaced archive',best.render([],3,issues))

    def test_numerically_small_result_without_qualification_is_not_a_win(self):
        p=self.receipt(program_size=100,hutter_score=1000)
        data=json.loads(p.read_text());data['data_size']=1000000000;p.write_text(json.dumps(data))
        row=evidence.load_row(p)
        self.assertFalse(row.full_corpus_proof)
        with patch.object(evidence,'ROOT',self.root):rendered=evidence.render([row],3)
        self.assertIn('target reached by this matrix: `False`',rendered)


if __name__=='__main__':unittest.main()
