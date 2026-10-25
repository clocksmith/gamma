import importlib.util
from pathlib import Path
import sys
import unittest

SPEC=importlib.util.spec_from_file_location('description_guard',Path(__file__).with_name('guard.py'))
g=importlib.util.module_from_spec(SPEC);sys.modules[SPEC.name]=g;SPEC.loader.exec_module(g)


def contract(**values): return {'facts':values,'conflicts':[],'evidence':[]}

class GuardTests(unittest.TestCase):
    def test_full_clause_grammar_and_spans(self):
        text='  Return all indices. The graph is directed; do not mutate the input.'
        p=g.parse_query(text)
        self.assertTrue(p['grammar_complete'])
        self.assertEqual(p['facts'],{'returned_entity':'index','selection':'all','graph_direction':'directed','input_mutation':'forbidden'})
        for e in p['evidence']:
            self.assertEqual(text[e['start']:e['end']],e['span'])
            self.assertEqual(g.sha(text.encode()),e['text_sha256'])

    def test_negation_conditional_quotes_and_near_misses_unknown(self):
        for s in ('Do not return indices','If possible return indices', '"Return indices"',
                  'The graph is not directed', 'Return values or indices',
                  'Return the number of indices', 'Return indices unless no match',
                  'Return values?','Return all index values'):
            with self.subTest(s=s):
                p=g.parse_query(s)
                self.assertFalse(p['grammar_complete']);self.assertEqual(p['facts'],{})

    def test_explicit_oppositions(self):
        pairs=[('Return indices','returned_entity','value'),
               ('Return all values','selection','one'),
               ('The graph is directed','graph_direction','undirected'),
               ('Input mutation is required','input_mutation','forbidden'),
               ('Return the same input array','output_alias','fresh'),
               ('Return an integer','result_shape','integer-array')]
        for q,f,v in pairs:
            with self.subTest(f=f):
                r=g.compare(g.parse_query(q),contract(**{f:v}))
                self.assertEqual(r['facets'][f],'violated')

    def test_unknown_is_not_false_or_satisfied(self):
        p=g.parse_query('Return values')
        r=g.compare(p,contract())
        self.assertEqual(r['overall'],'unknown');self.assertEqual(r['contradictions'],[])
        r=g.compare(p,contract(returned_entity='value'))
        self.assertEqual(r['facets']['returned_entity'],'satisfied')
        self.assertEqual(r['overall'],'unknown')

    def test_conflict_abstains_without_service(self):
        class Service:
            def request(self,*args,**kwargs): raise AssertionError('must not retrieve')
        ids=['a','b']; cs={x:contract() for x in ids}
        r=g.guarded_decide('Return values; Return indices',[('a',.9),('b',.1)],
                           {'min_cosine':.1,'min_margin':.1},Service(),ids,cs)
        self.assertEqual(r['status'],'abstain');self.assertEqual(r['clarification_questions'],[])

    def test_domain_inclusion_is_not_symmetric_inequality(self):
        self.assertEqual(g.compare(g.parse_query('Input array is sorted'),contract(input_order='arbitrary'))['facets']['input_order'],'satisfied')
        self.assertEqual(g.compare(g.parse_query('Input array is arbitrary'),contract(input_order='sorted'))['facets']['input_order'],'violated')
        self.assertEqual(g.compare(g.parse_query('Input array is sorted'),contract(input_order='rotated-sorted'))['facets']['input_order'],'satisfied')

    def test_unknown_competitors_retained(self):
        ids=[str(i) for i in range(4081)]
        cs={x:contract() for x in ids};cs['0']=contract(returned_entity='index')
        kept=g.filter_candidates(ids,cs,g.parse_query('Return values'))
        self.assertEqual(len(kept),4080);self.assertNotIn('0',kept)
        self.assertEqual(g.filter_candidates(ids,cs,g.parse_query('Do not return values')),frozenset(ids))
        self.assertEqual(g.filter_candidates(ids,cs,g.parse_query('Maybe. Return values')),frozenset(ids))

    def test_structured_contract_provenance_and_no_title_inference(self):
        text='Return indices\nObjective: "Minimum input element."\nResult: {"type":"integer"}\nInput domain: {}\n'
        c=g.contract_facts({'text':text})
        self.assertEqual(c['facts'],{'result_shape':'scalar-integer','returned_entity':'value'})
        self.assertNotIn('input_mutation',c['facts'])
        self.assertEqual(g.contract_facts({'text':'Directed Graph Return All Indices'})['facts'],{})
        for e in c['evidence']: self.assertEqual(text[e['start']:e['end']],e['span'])

    def test_veto_does_not_select_runner_up(self):
        class Service:
            def request(self,*args,**kwargs): raise AssertionError('must not retrieve')
        ids=['a','b'];cs={'a':contract(returned_entity='index'),'b':contract(returned_entity='value')}
        r=g.guarded_decide('Return values',[('a',.95),('b',.2)],{'min_cosine':.1,'min_margin':.1},Service(),ids,cs)
        self.assertEqual(r['status'],'abstain')

    def test_original_retrieval_and_unknown_preserved(self):
        calls=[]
        class Service:
            def request(self,pid,**kw):
                calls.append((pid,kw))
                return {'status':'matched','consumer_selection':{'status':'selected','exact_receipt':'fixture'}}
        ids=['a','b'];cs={x:contract() for x in ids}
        r=g.guarded_decide('Some unrestricted description',[('a',.95),('b',.2)],{'min_cosine':.1,'min_margin':.1},Service(),ids,cs)
        self.assertEqual(r['status'],'accepted');self.assertFalse(r['semantic_proof'])
        self.assertFalse(r['recognition_qualified']);self.assertEqual(len(calls),3)
        self.assertEqual(r['guard']['overall'],'unknown')
        self.assertEqual(r['implementations']['python']['exact_receipt'],'fixture')

    def test_missing_population_rejected(self):
        with self.assertRaises(ValueError):
            g.guarded_decide('Return values',[('a',.9),('b',.1)],{},None,['a','b','c'],{})

    def test_gate_denial_precedes_combined_document_open(self):
        from unittest.mock import patch
        reads=[]
        def pinned(spec):
            reads.append(spec['path'])
            if spec['path']=='plan':
                return {'boundary_gate':{'path':'gate'},'authorities':[{'problem_id':'leetcode:1'}]}
            if spec['path']=='gate': return {'artifact_paths':{},'trusted_hashes':{}}
            raise AssertionError('unauthorized combined payload opened')
        with patch.object(g,'pinned_metadata',side_effect=pinned), patch.object(g,'authorize_before_open',side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                g.load_documents({'path':'plan'},{'path':'documents'})
        self.assertEqual(reads,['plan','gate'])

    def test_unsorted_and_duplicate_ranking_rejected(self):
        ids=['a','b'];cs={x:contract() for x in ids}
        for ranking in ([('a',.2),('b',.9)],[('a',.9),('a',.2)]):
            with self.assertRaises(ValueError):
                g.guarded_decide('Return values',ranking,{},None,ids,cs)

    def test_all_grammar_rules_are_live(self):
        examples=['Return value','Output indices','Return all elements','Output all indices',
                  'Return one element','Return a single index','The graph is directed',
                  'Graph is undirected','Input array is sorted','Input array is arbitrary',
                  'Input array is rotated sorted','Input mutation is required',
                  'Input mutation is forbidden','Return a new array','Return same input array',
                  'Return a boolean','Return an integer','Return a string','Return an integer array']
        rules=set()
        for text in examples:
            p=g.parse_query(text);self.assertTrue(p['grammar_complete'],text)
            rules.update(e['rule'] for e in p['evidence'])
        self.assertEqual(rules,{f'query-{i}' for i in range(len(g.QUERY_RULES))})

    def test_bounds_and_empty(self):
        for s in ('',' ','.','x'*32769):
            if s=='.': self.assertFalse(g.parse_query(s)['grammar_complete'])
            else:
                with self.assertRaises(ValueError): g.parse_query(s)

if __name__=='__main__':unittest.main()
