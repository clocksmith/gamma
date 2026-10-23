import base64
import json
import subprocess
import unittest
import codec
import search

TEXT='function solve(a){let result=0;for(let index=0;index<7;index++){result+=a*a+a*a}return result}'

class TemplateTests(unittest.TestCase):
    def nodes(self,text):return codec.extract({'x':text})['x']
    def decode(self,keys,tokens):return codec.decode_many(keys,{'x':{'tokens':tokens}},8)['x']
    def test_repeated_identifier_is_charged_once_per_template(self):
        nodes=self.nodes(TEXT);node=next(n for n in nodes if TEXT[n['start']:n['end']]=='a*a+a*a')
        self.assertEqual(node['args'],['a']);self.assertEqual(node['spec']['uses'],[0,0,0,0])
        keys=codec.order([codec.literal(x) for x in codec.ALPHABET]+[node['key']])
        plan=codec.encode_source(TEXT,nodes,keys)
        self.assertEqual(plan['constructor_codes'],1);self.assertEqual(plan['argument_codes'],1);self.assertEqual(plan['repeated_identifier_bytes'],3);self.assertLess(plan['selections'],len(TEXT))
        self.assertEqual(self.decode(keys,plan['tokens']),TEXT)
        where=plan['tokens'].index(node['key']);self.assertEqual(plan['tokens'][where+1],codec.literal('a'))
    def test_alpha_equivalent_patterns_share_metadata(self):
        a=self.nodes(TEXT);other=TEXT.replace('a','z');b=self.nodes(other)
        ka={n['key'] for n in a if n['spec']};kb={n['key'] for n in b if n['spec']}
        self.assertTrue(ka&kb)
    def test_different_names_have_separate_arguments(self):
        text=TEXT.replace('a*a+a*a','a*result+a*result');n=next(n for n in self.nodes(text) if text[n['start']:n['end']]=='a*result+a*result')
        self.assertEqual(n['args'],['a','result']);self.assertEqual(n['spec']['uses'],[0,1,0,1])
    def test_property_names_and_builtins_stay_fixed(self):
        text='function solve(a){let answer=0;answer=Math.max(a.length,a.length);return answer+100}'
        n=next(n for n in self.nodes(text) if text[n['start']:n['end']]=='Math.max(a.length,a.length)')
        self.assertEqual(n['args'],['a']);self.assertIn('Math.max(',''.join(n['spec']['parts']));self.assertIn('.length',''.join(n['spec']['parts']))
    def test_whole_body_and_free_byte_guard(self):
        text='function solve(a){return a*a+a*a}'
        nodes=self.nodes(text);self.assertTrue(all(not n['spec'] for n in nodes if text[n['start']:n['end']]=='return a*a+a*a'))
        self.assertTrue(all(n['free_bytes']*2<len(text) for n in nodes if n['spec']))
    def test_missing_identifier_literal_disables_template(self):
        text=TEXT.replace('a*a+a*a','longname*longname+longname*longname');nodes=self.nodes(text)
        n=next(n for n in nodes if text[n['start']:n['end']]=='longname*longname+longname*longname')
        keys=codec.order([codec.literal(x) for x in codec.ALPHABET]+[n['key']])
        plan=codec.encode_source(text,nodes,keys);self.assertEqual(plan['constructor_codes'],0)
    def test_literal_span_proposals_never_cross_template_region(self):
        nodes=self.nodes(TEXT);n=next(n for n in nodes if TEXT[n['start']:n['end']]=='a*a+a*a');keys=codec.order([codec.literal(x) for x in codec.ALPHABET]+[n['key']])
        plan=codec.encode_source(TEXT,nodes,keys)
        self.assertFalse(any(a<n['end'] and b>n['start'] for a,b,_ in plan['literal_spans']))
    def test_bad_constructor_argument_and_truncation(self):
        nodes=self.nodes(TEXT);n=next(n for n in nodes if TEXT[n['start']:n['end']]=='a*a+a*a');keys=codec.order([codec.literal(x) for x in codec.ALPHABET]+[n['key']]);plan=codec.encode_source(TEXT,nodes,keys)
        pos=plan['tokens'].index(n['key']);bad=list(plan['tokens']);bad[pos+1]=codec.literal('+')
        with self.assertRaises(subprocess.CalledProcessError):self.decode(keys,bad)
        with self.assertRaises(subprocess.CalledProcessError):self.decode(keys,[n['key']])
    def test_independent_whole_template_rejection(self):
        spec={'kind':'ReturnStatement','parts':['return ','*','+','*',''],'uses':[0,0,0,0],'arity':1}
        key=codec.constructor(spec);keys=codec.order([codec.literal(x) for x in codec.ALPHABET]+[key])
        tokens=[codec.literal(x) for x in 'function solve(a){']+[key,codec.literal('a'),codec.literal('}')]
        with self.assertRaises(subprocess.CalledProcessError):self.decode(keys,tokens)
    def test_decoder_rejects_hole_embedded_in_larger_identifier(self):
        spec={'kind':'CallExpression','parts':['f(','x)'],'uses':[0],'arity':1};key=codec.constructor(spec)
        keys=codec.order([codec.literal(x) for x in codec.ALPHABET]+[key])
        tokens=[codec.literal(x) for x in 'function solve(a){let longEnough=0;return ']+[key,codec.literal('a'),codec.literal('}')]
        with self.assertRaises(subprocess.CalledProcessError):self.decode(keys,tokens)
    def test_escaped_identifier_spelling_is_never_replaced(self):
        text=r'function solve(a){let answer=0;answer=\u0061*\u0061+\u0061;return answer}'
        nodes=self.nodes(text)
        for n in nodes:
            if n['spec']:
                out=n['spec']['parts'][0]
                for i,use in enumerate(n['spec']['uses']):out+=n['args'][use]+n['spec']['parts'][i+1]
                self.assertEqual(out,text[n['start']:n['end']])
    def test_cached_and_uncached_evaluation_match(self):
        texts={'x':TEXT,'y':TEXT+';'};nodes=codec.extract(texts);base=[codec.literal(x) for x in codec.ALPHABET];ctors,lp,_=search.pool(texts,nodes,set(texts.values()));self.assertTrue(ctors)
        budget=search.Budget(100,60);old=search.evaluate(texts,nodes,base,budget)
        got=search.evaluate(texts,nodes,base+[ctors[0]],budget,old);fresh=search.evaluate(texts,nodes,base+[ctors[0]],budget)
        self.assertEqual(got,fresh)

if __name__=='__main__':unittest.main()
