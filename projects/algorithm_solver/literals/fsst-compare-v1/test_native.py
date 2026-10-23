import itertools
import os
import random
import unittest
import native
import packet

LIB='/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1/fsst-comparator-build/libgamma_fsst.so'


def all_paths(table,text):
    if not text:return [b'']
    paths=[bytes((255,text[0]))+tail for tail in all_paths(table,text[1:])]
    for i,word in enumerate(table):
        if text.startswith(word):paths += [bytes((i,))+tail for tail in all_paths(table,text[len(word):])]
    return paths

class FSSTTests(unittest.TestCase):
    def test_exact_native_dp_exhaustive(self):
        rng=random.Random(19)
        for _ in range(100):
            table=rng.sample([b'a',b'b',b'ab',b'ba',b'aa',b'bb',b'aba'],rng.randint(0,7))
            text=bytes(rng.choice(b'ab') for _ in range(rng.randint(0,7)))
            encoded=native.optimal(table,text);self.assertEqual(encoded,min(all_paths(table,text),key=lambda p:(len(p),p)))
            self.assertEqual(native.decode(table,encoded),text)
    def test_author_encoder_binary_and_optimal_roundtrip(self):
        fit=[b'function sample(input){return input.map(x=>x+1)}'*4+str(i%10).encode() for i in range(200)]
        targets=fit[:5]+[bytes(range(256)),b'\0\xff\0',b'',b'changed context']
        with native.Encoder(LIB,fit) as enc:
            payloads=enc.compress(targets)
            for text,payload in zip(targets,payloads):
                optimal=native.optimal(enc.table,text)
                self.assertLessEqual(len(optimal),len(payload));enc.verify_official(optimal,text)
                self.assertEqual(packet.unpack(enc.header,packet.pack(enc.header,optimal)),text)
                counts=native.counts(enc.table,payload);self.assertEqual(counts['selections'],len(payload))
    def test_table_repeatability(self):
        fit=[b'abacabacaba'*100,b'hello hello hello'*100]
        with native.Encoder(LIB,fit) as a,native.Encoder(LIB,fit) as b:self.assertEqual(a.header,b.header)
    def test_escape_charges_two_codes(self):
        encoded=native.optimal([b'ab'],b'abz')
        self.assertEqual(encoded,b'\0\xffz');self.assertEqual(native.counts([b'ab'],encoded)['single_character_channel_codes'],2)
    def test_adapter_owner_body_and_capacity_rules(self):
        import run
        table=[b'ab',b'abc',b'zz',b'q'];fit={'1':'abcabcq','2':'abcabc','3':'zz'}
        pool,adapted=run.pool_and_adapter(table,[b'\1\1\3',b'\1\1',b'\2'],fit,{'abc'})
        self.assertEqual(pool,['ab']);self.assertEqual(len(adapted),97)
        self.assertTrue(run.v3.FALLBACK<=set(adapted))
    def test_prune_cap_retains_incumbent(self):
        import run
        budget=run.v3.Budget({'trials':1,'seconds':60});budget.trials=1;state={'sentinel':True}
        out,removed=run.capped_prune({},state,8,budget)
        self.assertIs(out,state);self.assertEqual(removed,[]);self.assertEqual(budget.trials,1)
    def test_bad_native_payloads_fail_closed(self):
        for payload in (b'\xff',b'\1'):
            with self.assertRaises(ValueError):native.decode([b'ab'],payload)
    def test_bad_frames_and_headers_fail_closed(self):
        with native.Encoder(LIB,[b'ababab'*100,b'ababab'*100]) as enc:
            payload=enc.compress([b'abab'])[0];p=packet.pack(enc.header,payload)
            for bad in (p[:-1],p+b'x',b'bad!'+p[4:],p[:40]+b'\7'+p[41:]):
                with self.assertRaises(ValueError):packet.unpack(enc.header,bad)
            with self.assertRaises(ValueError):native.table_from_header(enc.header[:-1])

if __name__=='__main__':unittest.main()
