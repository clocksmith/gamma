"""Repair scope and exact source/public evidence; no expected-value invention."""
from dataclasses import replace
import unittest
from algsolve.records import Problem
from algsolve.imported_examples import repair


def sample():
    return Problem('lcd:1','lcd','1','Fixture','fixture',
                   'Input: s = "  a   b "\nOutput: 3\n','functional',
                   starter_code='class Solution:\n def count(self, s: str) -> int:\n  pass\n',
                   entry={'class':'Solution','method':'count'},params=[['s','str']],
                   public_tests=[{'args':[' a b '],'expected':3,'compare':'return'}],
                   import_notes={'lcd_split':'train'},hidden_tests_path='must-not-read',
                   reference_solutions=['must-not-read'])


class ImportedExamplesTests(unittest.TestCase):
    def test_exact_historical_input_transform_is_restored_without_mutation(self):
        original=sample();new,receipt=repair(original)
        self.assertTrue(receipt['changed'])
        self.assertEqual(new.public_tests[0]['args'],['  a   b '])
        self.assertEqual(original.public_tests[0]['args'],[' a b '])
        self.assertEqual(new.public_tests[0]['expected'],original.public_tests[0]['expected'])
        self.assertEqual(new.hidden_tests_path,'must-not-read')

    def test_different_value_expected_count_and_incomplete_examples_fail_closed(self):
        p=sample()
        for q in [replace(p,public_tests=[{'args':['wrong'],'expected':3,'compare':'return'}]),
                  replace(p,public_tests=[{'args':[' a b '],'expected':4,'compare':'return'}]),
                  replace(p,statement=p.statement+'Input: s = "x"\n'),
                  replace(p,statement=p.statement+'Input: s = "x"\nOutput: 1\n')]:
            with self.subTest(q=q.statement):
                new,receipt=repair(q);self.assertIs(new,q);self.assertFalse(receipt['changed'])

    def test_user_examples_or_missing_source_provenance_are_not_rewritten(self):
        p=sample()
        for q in [replace(p,source='user'),replace(p,uid='lcd:2'),replace(p,import_notes={})]:
            with self.subTest(source=q.source):
                new,receipt=repair(q);self.assertIs(new,q);self.assertFalse(receipt['changed'])

    def test_escaped_whitespace_is_not_mistaken_for_source_layout(self):
        p=replace(sample(),statement='Input: s = "a\\tb"\nOutput: 3\n',
                  public_tests=[{'args':['a b'],'expected':3,'compare':'return'}])
        new,receipt=repair(p);self.assertFalse(receipt['changed']);self.assertIs(new,p)
