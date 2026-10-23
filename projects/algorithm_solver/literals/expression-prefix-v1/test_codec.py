import base64
import json
import subprocess
import unittest
import codec as c


class PrefixCodecTests(unittest.TestCase):
    def setUp(self):self.alphabet=[c.literal(x) for x in c.ALPHABET]

    def nodes(self,text):return c.extract({'x':text})['x']

    def keys(self,nodes):return c.order(self.alphabet+[c.constructor(n['spec']) for n in nodes if n['spec']])

    def decode(self,keys,packet):
        value={'dictionary':base64.b64encode(c.dictionary(keys)).decode(),'packets':{'x':base64.b64encode(packet).decode()}}
        return subprocess.run(['node',str(c.HERE/'decoder.cjs')],input=json.dumps(value),text=True,capture_output=True)

    def test_roundtrip_nested_operands_and_action_savings(self):
        text='function solve(a,b){return Math.max(a.length,b.length)}'
        nodes=self.nodes(text);keys=self.keys(nodes)
        plain=c.encode_source(text,nodes,self.alphabet);typed=c.encode_source(text,nodes,keys)
        self.assertLess(typed['selections'],plain['selections']);self.assertGreater(typed['constructor_codes'],0)
        self.assertEqual(c.decode_many(keys,{'x':typed},7)['x'],text)
        self.assertEqual(typed['selections'],len(typed['tokens']))

    def test_complete_expression_literal_and_precedence(self):
        text='function solve(a,b,c){return (a+b)*c}'
        nodes=self.nodes(text);keys=self.keys(nodes)
        result=c.encode_source(text,nodes,keys)
        self.assertEqual(c.decode_many(keys,{'x':result},7)['x'],text)
        mult=next(c.constructor(n['spec']) for n in nodes if n['spec'] and n['spec']['fields'].get('operator')=='*')
        keys=c.order(keys+[c.literal('a+b')])
        bad=c.packet(keys,[mult,c.literal('a+b'),c.literal('c')],7)
        self.assertNotEqual(self.decode(keys,bad).returncode,0)

    def test_raw_fragment_is_not_expression_operand(self):
        nodes=self.nodes('function solve(a){return a.length}')
        key=next(c.constructor(n['spec']) for n in nodes if n['spec'])
        keys=c.order(self.alphabet+[key,c.literal('return')])
        self.assertNotEqual(self.decode(keys,c.packet(keys,[key,c.literal('return')],7)).returncode,0)

    def test_truncation_wrong_dictionary_and_padding_rejected(self):
        keys=self.alphabet;packet=c.packet(keys,[c.literal('a')],7)
        self.assertNotEqual(self.decode(keys,packet[:-1]).returncode,0)
        wrong=bytearray(packet);wrong[5]^=1
        self.assertNotEqual(self.decode(keys,bytes(wrong)).returncode,0)
        wrong=bytearray(packet);wrong[-1]|=1
        self.assertNotEqual(self.decode(keys,bytes(wrong)).returncode,0)

    def test_unsupported_child_falls_back_without_free_bytes(self):
        text='function solve(a){return Math.max(a,12345)}';nodes=self.nodes(text);keys=self.keys(nodes)
        row=c.encode_source(text,nodes,keys)
        self.assertEqual(c.decode_many(keys,{'x':row},7)['x'],text)
        self.assertTrue(any(k==c.literal('1') for k in row['tokens']))

    def test_literal_only_matches_independent_canonical_dp(self):
        import sys
        sys.path.insert(0,str(c.HERE.parent));from literals import shortest_encode
        text='function solve(a){return a+a}';nodes=self.nodes(text)
        vocab=c.ALPHABET+['function solve(','return ','a+a'];keys=c.order([c.literal(x) for x in vocab])
        row=c.encode_source(text,nodes,keys)
        self.assertEqual(row['selections'],len(shortest_encode(text,[x[1:] for x in keys])))

    def test_cache_recomputes_constructor_changes(self):
        import search
        text='function solve(a){return a.length}';texts={1:text};nodes={'1':self.nodes(text)}
        for node in nodes['1']:node['key']=c.constructor(node['spec']) if node['spec'] else None
        budget=search.Budget(100,30)
        start=search.evaluate(texts,nodes,self.alphabet,budget)
        keys=self.keys(nodes['1'])
        cached=search.evaluate(texts,nodes,keys,budget,start);full=search.evaluate(texts,nodes,keys,budget)
        self.assertEqual(cached['rows'],full['rows']);self.assertLess(cached['selections'],start['selections'])

    def test_optional_chain_context_does_not_forge_member_type(self):
        text='function solve(a){return a?.length}';nodes=self.nodes(text);keys=self.keys(nodes)
        row=c.encode_source(text,nodes,keys)
        self.assertEqual(c.decode_many(keys,{'x':row},7)['x'],text)

    def test_budget_retains_improved_complete_incumbent(self):
        import search
        texts={1:'function solve(a){return a.length}',2:'function solve(b){return b.length}'}
        nodes=c.extract(texts)
        constructors,expressions,_=search.pool(texts,nodes,set(texts.values()))
        initial=sum(c.encode_source(t,nodes[str(p)],self.alphabet)['selections'] for p,t in texts.items())
        state,info=search.optimize(texts,nodes,self.alphabet,7,constructors,expressions,set(texts.values()),{'trials':8,'seconds':30})
        self.assertEqual(info['stop'],'trial_limit');self.assertEqual(info['trials'],8)
        self.assertLess(state['selections'],initial)
        self.assertEqual(c.decode_many(state['keys'],state['rows'],7),{str(p):t for p,t in texts.items()})


if __name__=='__main__':unittest.main()
