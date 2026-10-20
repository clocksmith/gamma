"""Tracked-safe synthetic parser controls; no corpus or independent-test access."""
import copy
import hashlib
import unittest
from dataclasses import replace
from unittest.mock import patch
from algsolve import importers, imported_examples as repairs, editor_task
from algsolve.public_examples import recover
from algsolve.records import Problem


def problem(statement='Input: old = [1, 2]\nOutput: 3\n'):
    return Problem(uid='lcd:synthetic-public-repair', source='lcd',
        source_id='synthetic-public-repair', title='Synthetic literal fixture',
        slug='synthetic-literal-fixture', statement=statement, io_mode='functional',
        starter_code='class Solution:\n    def solve(self, new: List[int]) -> int:\n        pass\n',
        entry={'class':'Solution','method':'solve'}, params=[['new','List[int]']],
        import_notes={'lcd_split':'train'})


def pin(p, **extra):
    return dict(statement_sha256=hashlib.sha256(p.statement.encode()).hexdigest(),
        interface_sha256=repairs._digest([p.entry,p.params,p.starter_code]),
        parameter_aliases={'old':'new'}, duplicate_output_label=False,
        example_count=1, **extra)


class SyntheticPublicRepairs(unittest.TestCase):
    def test_default_path_does_not_guess_alias(self):
        p=problem();self.assertEqual(recover(p).public_tests,[])
        q,r=repairs.repair(p);self.assertIs(q,p);self.assertFalse(r['changed'])
    def test_repair_preserves_original_and_all_other_fields(self):
        p=problem();before=copy.deepcopy(p.__dict__)
        with patch.dict(repairs._PUBLIC_LITERAL_REPAIRS,{p.uid:pin(p)}):q,r=repairs.repair(p)
        self.assertTrue(r['changed']);self.assertEqual(p.__dict__,before)
        self.assertEqual(q.public_tests,[{'args':[[1,2]],'expected':3,'compare':'return'}])
        self.assertEqual(replace(q,public_tests=[]),p)
    def test_alias_keys_never_change_string_data(self):
        t,d=importers.statement_examples('Input: old = "old =  x  "\nOutput: "old =  x  "\n',
            [('new','str')],'str',parameter_aliases={'old':'new'})
        self.assertEqual(d,0);self.assertEqual(t,[{'args':['old =  x  '],'expected':'old =  x  ','compare':'return'}])
    def test_alias_collision_and_bad_target_fail(self):
        for aliases in [{'old':'new'},{'old':'missing'},{'old':'new','other':'new'}]:
            with self.subTest(aliases=aliases):
                t,d=importers.statement_examples('Input: old = 1, new = 2\nOutput: 1\n',
                    [('new','int')],'int',parameter_aliases=aliases)
                self.assertEqual((t,d),([],1))
    def test_unknown_arguments_fail(self):
        t,d=importers.statement_examples('Input: old = 1, surprise = 2\nOutput: 1\n',
            [('new','int')],'int',parameter_aliases={'old':'new'})
        self.assertEqual((t,d),([],1))
    def test_duplicate_label_requires_opt_in(self):
        s='Input: n = 1\nOutput: Output: 1\n'
        self.assertEqual(importers.statement_examples(s,[('n','int')],'int'),([],1))
        t,d=importers.statement_examples(s,[('n','int')],'int',duplicate_output_label=True)
        self.assertEqual((t,d),([{'args':[1],'expected':1,'compare':'return'}],0))
    def test_duplicate_label_preserves_quoted_literal(self):
        t,d=importers.statement_examples('Input: n = 1\nOutput: "Output: preserve"\n',
            [('n','int')],'str',duplicate_output_label=True)
        self.assertEqual(d,0);self.assertEqual(t[0]['expected'],'Output: preserve')
        self.assertEqual(importers.statement_examples('Input: n = 1\nOutput: Output: Output: 1\n',
            [('n','int')],'int',duplicate_output_label=True),([],1))
    def test_hash_mismatch_fails(self):
        p=problem()
        with patch.dict(repairs._PUBLIC_LITERAL_REPAIRS,{p.uid:pin(p)}):
            for q in [replace(p,statement=p.statement+'\n'),replace(p,params=[['changed','List[int]']]),replace(p,starter_code=p.starter_code+'#changed')]:
                with self.subTest(params=q.params):
                    out,r=repairs.repair(q);self.assertIs(out,q);self.assertFalse(r['changed'])
                    self.assertEqual(r['reason'],'pinned_public_source_mismatch')
    def test_existing_examples_and_wrong_provenance_preserved(self):
        p=problem()
        with patch.dict(repairs._PUBLIC_LITERAL_REPAIRS,{p.uid:pin(p)}):
            for q in [replace(p,public_tests=[{'args':[],'expected':'keep'}]),replace(p,source='user'),replace(p,source_id='other'),replace(p,import_notes={}),replace(p,io_mode='stdin')]:
                out,r=repairs.repair(q);self.assertIs(out,q);self.assertFalse(r['changed'])
    def test_complete_example_requirement_not_bypassed(self):
        p=problem('Input: old = [1, 2]\nOutput: 3\nInput: old = [4]\n')
        with patch.dict(repairs._PUBLIC_LITERAL_REPAIRS,{p.uid:pin(p)}):
            q,r=repairs.repair(p)
        self.assertIs(q,p);self.assertFalse(r['changed']);self.assertEqual(r['reason'],'incomplete_pinned_public_examples')
    def test_known_source_caller_supplies_pinned_examples(self):
        p=problem()
        with patch.dict(repairs._PUBLIC_LITERAL_REPAIRS,{p.uid:pin(p)}):
            q=editor_task._known_source_public(p,p)
        self.assertEqual(q.public_tests,[{'args':[[1,2]],'expected':3,'compare':'return'}])
        self.assertFalse(p.public_tests)
    def test_known_source_caller_rejects_entry_drift(self):
        p=problem()
        with patch.dict(repairs._PUBLIC_LITERAL_REPAIRS,{p.uid:pin(p)}):
            for e in [replace(p,statement=p.statement+'changed'),replace(p,entry={'class':'Solution','method':'other'}),replace(p,params=[['other','int']]),replace(p,starter_code=p.starter_code+'#changed')]:
                self.assertIs(editor_task._known_source_public(e,p),p)
    def test_known_source_caller_preserves_existing_and_untrusted_packets(self):
        p=problem()
        with patch.dict(repairs._PUBLIC_LITERAL_REPAIRS,{p.uid:pin(p)}):
            for q in [replace(p,source='user'),replace(p,public_tests=[{'args':[],'expected':'keep'}])]:
                self.assertIs(editor_task._known_source_public(q,q),q)
    def test_executable_expression_rejected(self):
        t,d=importers.statement_examples('Input: old = __import__("os").getpid()\nOutput: 1\n',
            [('new','int')],'int',parameter_aliases={'old':'new'})
        self.assertEqual((t,d),([],1))

if __name__=='__main__':unittest.main(verbosity=2)
