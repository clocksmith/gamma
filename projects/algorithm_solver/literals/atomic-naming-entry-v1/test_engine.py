import unittest
import core as c
import engine
import proof


class EngineTests(unittest.TestCase):
    def test_geometry_rejects_partial_identifier_and_string_occurrence(self):
        text='function solve(longName){return longName+1;}'
        rec=c.rewrite.records({'0':text})['0'];var=next(v for v in rec['variables'] if v['name']=='longName')
        a,b=var['spans'][-1]
        self.assertIsNone(c.pattern_at(text,var['spans'],a+1,b))
        self.assertIsNone(c.pattern_at(text,var['spans'],a,b-1))
        self.assertEqual(c.pattern_at(text,var['spans'],a,b),['',None,''])
        source='function solve(a){return "a+a"+a;}'
        rec=c.rewrite.records({'0':source})['0']
        self.assertEqual(engine.validation_matches(source,rec,['',None,'+',None,'']),[])
        captured='function solve(a){return a+aa;}'
        rec=c.rewrite.records({'0':captured})['0'];bid=next(v['id'] for v in rec['variables'] if v['name']=='a')
        self.assertIsNone(c.make_group({'0':captured},{'0':rec},{'pattern':['',None,''],'matches':[['0',bid]]},'aa',min_support=1))

    def test_non_ascii_utf16_spans_never_enter_naming(self):
        source='function solve(a){let s="😀";return a+1;}'
        rec=c.rewrite.records({'0':source})['0'];bid=next(v['id'] for v in rec['variables'] if v['name']=='a')
        self.assertEqual(engine.validation_matches(source,rec,['function solve(',None,')']),[])
        self.assertIsNone(c.make_group({'0':source},{'0':rec},{'pattern':['function solve(',None,')'],'matches':[['0',bid]]},'aa',min_support=1))

    def test_new_rejected_variant_ban_invalidates_incumbent(self):
        original='function solve(a){return a+1;}'
        changed='function solve(aa){return aa+1;}'
        vocab=c.order(c.ALPHABET+['{return aa+1;}'])
        state=c.evaluate({'0':original},vocab);ledger=c.BanLedger();ledger.encounter({'0':original},'initial');ledger.assert_incumbent(state)
        ledger.encounter({'0':changed},'rejected-proposal')
        with self.assertRaises(c.LegalityFailure):ledger.assert_incumbent(state)
        self.assertIn('{return aa+1;}',ledger.receipt()['banned'])
        self.assertEqual(len(ledger.receipt()['variants']),2)

    def test_exact_lex_cost_and_common_projection_rules(self):
        texts,renamed,seed,_=proof.fixture();state=c.evaluate(texts,seed)
        for pid,text in texts.items():
            n,chars,ids=proof.encode(text,state['vocab'])
            self.assertEqual(state['plans'][pid],[state['vocab'][i] for i in ids])
        records=c.rewrite.records(texts);contexts=c.contexts(state,records)
        context=next(x for x in contexts if x['pattern']==['',None,'+',None,''])
        group=c.make_group(texts,records,context,'aa');self.assertEqual(group['updates'],renamed)
        ledger=c.BanLedger();ledger.encounter(texts,'initial');ledger.encounter(renamed,'candidate')
        offered={arm:list(engine.streams(state,[group],ledger.forbidden,arm)) for arm in engine.ARMS}
        self.assertEqual([x for x in offered['A'] if x['kind']=='context_dictionary'],[x for x in offered['J'] if x['kind']=='context_dictionary'])
        self.assertEqual([x for x in offered['S'] if x['kind']=='source'],[x for x in offered['J'] if x['kind']=='source'])
        self.assertTrue(any(x['kind']=='joint' for x in offered['J']))
        self.assertFalse(any(x['kind']=='joint' for x in offered['A']))

    def test_rejected_low_support_variant_remains_encounterable(self):
        text='function solve(a){return a+1;}'
        records=c.rewrite.records({'0':text});var=next(v for v in records['0']['variables'] if v['name']=='a')
        group=c.make_group({'0':text},records,{'pattern':['',None,'+1'],'matches':[['0',var['id']]]},'aa')
        self.assertIsNotNone(group);self.assertFalse(group['eligible']);self.assertIn('0',group['updates'])

    def test_bounded_search_retains_actual_characters_and_exact_receipt(self):
        texts,_,seed,_=proof.fixture();snapshots=[]
        got=engine.optimize(texts,seed,['aa'],'J',{'trials':220,'seconds':10},lambda row:snapshots.append(row['trials']))
        self.assertTrue(got['complete']);self.assertLessEqual(got['trials'],220)
        state=got['state'];fresh=c.evaluate(state['sources'],state['vocab'])
        self.assertEqual(c.cost(state),c.cost(fresh))
        self.assertEqual({w for w in seed if len(w)==1},{w for w in state['vocab'] if len(w)==1})
        self.assertLess(c.cost(state),c.cost(c.evaluate(texts,seed)))
        self.assertTrue(snapshots)


if __name__=='__main__':unittest.main()
