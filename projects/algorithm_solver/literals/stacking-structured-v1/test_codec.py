import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('structured_stack_codec_test',HERE/'codec.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class UnionCodecTests(unittest.TestCase):
    def decode(self,keys,tokens=None,packet=None,db=None):
        db = c.dictionary(keys) if db is None else db
        packet = c.packet(keys,tokens) if packet is None else packet
        request = {'dictionary':base64.b64encode(db).decode(), 'packets':{'p':base64.b64encode(packet).decode()}}
        return subprocess.run(['node',str(HERE/'decoder.cjs')],input=json.dumps(request),text=True,capture_output=True)

    def prepared(self,text):
        nodes = c.extract({'p':text})['p']
        keys = c.order([c.literal(x) for x in c.ALPHABET]+[
            n['key'] for family in ('prefix','identifier') for n in nodes[family] if n['key']])
        return nodes,keys

    def test_union_roundtrip_and_paid_counts(self):
        text = 'function solve(a,b){let q=a.length;let r=b.length;return q+r+Math.max(a.length,b.length)}'
        nodes,keys = self.prepared(text)
        self.assertLessEqual(len(keys),256)
        plans = {}
        for name,allowed in [('literal',{'L'}),('prefix',{'L','P'}),('template',{'L','I'}),('union',{'L','P','I'})]:
            selected = c.order(k for k in keys if k[0] in allowed)
            plan = c.encode_source(text,nodes,selected)
            self.assertEqual(plan['selections'],len(plan['tokens']))
            self.assertEqual(plan['constructor_codes'],plan['prefix_codes']+plan['identifier_codes'])
            self.assertEqual(c.decode_many(selected,{'p':plan})['p'],text)
            self.assertEqual(len(c.packet(selected,plan['tokens'])),41+plan['selections'])
            plans[name] = plan
        self.assertLess(plans['union']['selections'],plans['literal']['selections'])
        self.assertLessEqual(plans['union']['selections'],plans['prefix']['selections'])
        self.assertLessEqual(plans['union']['selections'],plans['template']['selections'])
        self.assertGreater(plans['union']['prefix_codes']+plans['union']['identifier_codes'],0)

    def test_no_implicit_missing_characters(self):
        keys = c.order([c.literal('ab')])
        self.assertEqual(keys,[c.literal('ab')])
        nodes = {'bodies':[],'prefix':[],'identifier':[]}
        self.assertEqual(c.encode_source('abab',nodes,keys)['selections'],2)
        with self.assertRaises(ValueError):
            c.encode_source('ac',nodes,keys)

    def test_identifier_cannot_be_prefix_operand(self):
        p = c.constructor('P',{'fields':{'type':'BinaryExpression','operator':'+'},
                               'paths':[['left'],['right']],'parts':['','+','']})
        i = c.constructor('I',{'kind':'BinaryExpression','arity':1,'parts':['',' + ',''],'uses':[0,0]})
        keys = c.order([p,i,c.literal('a')])
        self.assertNotEqual(self.decode(keys,[p,i,c.literal('a'),c.literal('a')]).returncode,0)

    def test_identifier_arguments_are_literal_and_each_paid(self):
        i = c.constructor('I',{'kind':'BinaryExpression','arity':2,'parts':['',' + ',''],'uses':[0,1]})
        keys = c.order([i,c.literal('a')])
        self.assertNotEqual(self.decode(keys,[i,c.literal('a')]).returncode,0)
        self.assertNotEqual(self.decode(keys,[i,i,c.literal('a')]).returncode,0)

    def test_precedence_is_checked_independently(self):
        p = c.constructor('P',{'fields':{'type':'BinaryExpression','operator':'*'},
                               'paths':[['left'],['right']],'parts':['','*','']})
        keys = c.order([p,c.literal('a+b'),c.literal('c')])
        self.assertNotEqual(self.decode(keys,[p,c.literal('a+b'),c.literal('c')]).returncode,0)

    def test_whole_body_template_rejected(self):
        i = c.constructor('I',{'kind':'ReturnStatement','arity':1,'parts':['return ',';'],'uses':[0]})
        keys = c.order([i,c.literal('function solve(a){'),c.literal('a'),c.literal('}')])
        packet = [c.literal('function solve(a){'),i,c.literal('a'),c.literal('}')]
        self.assertNotEqual(self.decode(keys,packet).returncode,0)

    def test_framing_and_malformed_metadata_fail_closed(self):
        text = 'function solve(a){return a.length}'
        nodes,keys = self.prepared(text)
        plan = c.encode_source(text,nodes,keys)
        packet = c.packet(keys,plan['tokens'])
        self.assertNotEqual(self.decode(keys,packet=packet[:-1]).returncode,0)
        bad = bytearray(packet);bad[5] ^= 1
        self.assertNotEqual(self.decode(keys,packet=bytes(bad)).returncode,0)
        bad_entry = ['I',{'kind':'BinaryExpression','arity':1,'parts':['','+',''],'uses':[0,3]}]
        db = b'STD1'+json.dumps([bad_entry]).encode()
        raw = b'STB1'+bytes([8])+hashlib.sha256(db).digest()+struct.pack('>I',1)+bytes([0])
        self.assertNotEqual(self.decode([],packet=raw,db=db).returncode,0)

    def test_depth_limit(self):
        p = c.constructor('P',{'fields':{'type':'MemberExpression','computed':False,'optional':False},
                               'paths':[['object']],'parts':['','.length']})
        keys = c.order([p,c.literal('a')])
        self.assertNotEqual(self.decode(keys,[p]*9+[c.literal('a')]).returncode,0)

    def test_shared_prefix_template_overlap_chooses_nonoverlapping_path(self):
        text = 'function solve(a,b){let q=a.length;return q+b.length}'
        nodes,keys = self.prepared(text)
        plan = c.encode_source(text,nodes,keys)
        self.assertEqual(c.decode_many(keys,{'p':plan})['p'],text)
        spans = plan['literal_spans']
        self.assertTrue(all(left[1] <= right[0] for left,right in zip(spans,spans[1:])))


if __name__ == '__main__':
    unittest.main()
