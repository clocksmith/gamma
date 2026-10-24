"""Invented binding programs only; no private artifacts or cases."""
import unittest
from unittest.mock import patch
import common as c
import engine as e

TEXT='function solve(a){return a+a}'
MENU={'names':['aa'],'contexts':[{'pattern':['return ',None,'+',None,'']}]}

class EngineTests(unittest.TestCase):
    def test_fixed_order_and_existing_order_parity(self):
        vocab=['abc','dxx','ab','cdxx'];got=c.evaluate({'0':'abcdxx'},vocab)
        self.assertEqual(got['vocab'],vocab);self.assertEqual(got['plans']['0'],['abc','dxx'])
        ordered=c.p.order(vocab)
        self.assertEqual(c.evaluate({'0':'abcdxx'},ordered),c.p.evaluate({'0':'abcdxx'},ordered))
        self.assertEqual(c.p.evaluate({'0':'abcdxx'},vocab)['plans']['0'],['ab','cdxx'])

    def test_menu_rule_matches_frozen41(self):
        texts={'0':TEXT,'1':TEXT.replace('(a)','(b)').replace('a+a','b+b')}
        vocab=c.p.order(c.p.ALPHABET+['aa']);m=e.menu(texts,vocab);state=c.p.evaluate(texts,vocab);recs=c.rewrite.records(texts)
        self.assertEqual(m['names'],c.p.names(vocab,recs));self.assertEqual(m['contexts'],c.p.contexts(state,recs))

    def test_spelling_reduces_characters_at_unchanged_selections(self):
        vocab=list(reversed(c.p.ALPHABET))+['aa'];before=c.evaluate({'0':TEXT},vocab)
        got=e.apply({'0':TEXT},vocab,MENU);after=c.evaluate(got['selected'],vocab)
        self.assertEqual(after['N'],before['N']);self.assertLess(after['C'],before['C'])
        self.assertGreater(after['source_bytes'],before['source_bytes']);self.assertEqual(got['accepted'],1)
        self.assertEqual(got['vocab'],vocab);self.assertLessEqual(max(r['pass'] for r in got['trace']),1)

    def test_two_pass_limit_keeps_third_possible_improvement_unexplored(self):
        text='function solve(a,b,c){return a+a+b+b+c+c}'
        menu={'names':['aa','bb','cc'],'contexts':[
            {'pattern':['return ',None,'+',None,'+']},
            {'pattern':['+',None,'+',None,'+']},
            {'pattern':['+',None,'+',None,'}']}]}
        vocab=c.p.ALPHABET+['aa','bb','cc']
        got=e.apply({'0':text},vocab,menu)
        self.assertEqual(got['accepted'],2);self.assertEqual([r['pass'] for r in got['trace']],[0,1])
        diagnostic=e.apply(got['selected'],vocab,menu)
        self.assertGreater(diagnostic['accepted'],0)
        self.assertLess(c.evaluate(diagnostic['selected'],vocab)['C'],c.evaluate(got['selected'],vocab)['C'])

    def test_uncovered_proposal_retains_source(self):
        vocab=[w for w in c.p.ALPHABET if w!='z'];m={'names':['zz'],'contexts':MENU['contexts']}
        got=e.apply({'0':TEXT},vocab,m)
        self.assertEqual(got['selected'],{'0':TEXT});self.assertEqual(got['accepted'],0)
        self.assertTrue(got['trace'][0]['trials']);self.assertFalse(got['trace'][0]['trials'][0]['coverage'])
        self.assertEqual(len(got['ledger']['variants']),2)

    def test_initial_coverage_failure_cannot_be_rescued(self):
        vocab=[w for w in c.p.ALPHABET if w!='a']+['aa']
        got=e.apply({'0':TEXT},vocab,MENU)
        self.assertEqual(got['initial_coverage_failures'],['0']);self.assertEqual(got['proposals'],0)
        self.assertEqual(got['selected'],{'0':TEXT})

    def test_capture_and_nonascii_guard(self):
        vocab=c.p.ALPHABET+['aa'];text='function solve(a,aa){return a+aa}'
        menu={'names':['aa'],'contexts':[{'pattern':['return ',None,'+aa']}]}
        got=e.apply({'0':text},vocab,menu)
        self.assertEqual(got['selected'],{'0':text});self.assertEqual(got['accepted'],0)
        # The inherited lexical ban parser has an ASCII input contract. Test
        # the spelling guard itself, without claiming Unicode packet support.
        self.assertEqual(e.matches(TEXT+'/*é*/',{'unsafe':False},MENU['contexts'][0]['pattern']),[])

    def test_rejected_variant_ban_invalidates_other_dictionary(self):
        vocab=c.p.ALPHABET;renamed=TEXT.replace('(a)','(aa)').replace('a+a','aa+aa');checkpoints=[]
        with self.assertRaises(c.LegalityFailure):
            e.apply({'0':TEXT},vocab,MENU,checkpoint=checkpoints.append,
                    dictionaries={'own':vocab,'other':vocab+[renamed]})
        last=checkpoints[-1];self.assertFalse(last['complete']);self.assertEqual(last['accepted'],0)
        self.assertIn(renamed,last['ledger']['variants'].values())

    def test_global_union_retains_cross_arm_conflicts(self):
        ledger=c.BanLedger();ledger.encounter({'0':TEXT},'fit:initial')
        union=c.global_ledger([('24',ledger.receipt())],{'24':c.p.ALPHABET,'43N':[TEXT]})
        self.assertFalse(union['legal']);self.assertEqual(union['illegal_entry_sha256']['43N'],[c.sha(TEXT.encode())])

    def test_budget_failure_keeps_pending_evidence(self):
        checkpoints=[]
        with self.assertRaises(c.HardDeadline):e.apply({'0':TEXT},c.p.ALPHABET,MENU,checkpoint=checkpoints.append,proposal_cap=0)
        self.assertFalse(checkpoints[-1]['complete']);self.assertEqual(checkpoints[-1]['selected'],{'0':TEXT})

if __name__=='__main__':unittest.main()
