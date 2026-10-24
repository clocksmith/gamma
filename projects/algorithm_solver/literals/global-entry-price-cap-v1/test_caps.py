"""Small supplied q53/global-price checks; no corpus loader or measurement."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest
import caps
import proof
import test_proof


def fixture(texts,banned=(),seed=(),D=7,rng=None):
    banned=set(banned);rng=rng or random.Random(6607);owners={}
    for (pid,i,j),word in proof.parent.allowed(texts,banned).items():owners.setdefault(word,set()).add(pid)
    alphabet=sorted(set(''.join(texts.values()))|{'~'})
    pool=sorted(set(alphabet)|set(seed)|{word for word,pids in owners.items() if len(pids)>1})
    q=[rng.randrange(40) for pid,text in sorted(texts.items()) for start in range(len(text))
       for end in range(start+1,len(text)+1) if text[start:end] in pool]
    return dict(texts=texts,banned=banned,old_pool=pool,old_q=q,seed=list(seed),alphabet=alphabet,D=D,
        expected_source_hashes={pid:hashlib.sha256(text.encode()).hexdigest() for pid,text in texts.items()},expected_old_banned=banned)


def explicit(kw):
    texts,D=kw['texts'],kw['D'];values=iter(kw['old_q'])
    old={(pid,i,j):next(values) for pid,text in sorted(texts.items()) for i in range(len(text))
         for j in range(i+1,len(text)+1) if text[i:j] in kw['old_pool']}
    ds={}
    for pid,text in texts.items():
        d=[None]*len(text)+[0]
        for start in range(len(text)-1,-1,-1):
            d[start]=min(D*(9 if end-start==1 else -1)+old[pid,start,end]+d[end]
                         for end in range(start+1,len(text)+1) if (pid,start,end) in old)
        ds[pid]=d
    return {edge:max(0,ds[edge[0]][edge[1]]-ds[edge[0]][edge[2]]-D*(9 if edge[2]-edge[1]==1 else -1))
            for edge in proof.parent.allowed(texts,kw['banned'])}


class CapsTests(unittest.TestCase):
    def compare(self,kw,B=3,exhaustive=False):
        got=caps.check(**kw,capacity=B);q=explicit(kw);prices=[0]+[kw['D']*2**r for r in range(14)]
        oracle=(test_proof.ProofTests().check(kw['texts'],kw['banned'],q,prices,B,kw['D'])[0] if exhaustive else
                proof.certificate(kw['texts'],kw['banned'],q,prices,B,kw['D']))
        self.assertEqual(got['lambda_family'],prices)
        self.assertEqual(got['price_prefix_schedule'],oracle['price_schedules'])
        self.assertEqual(got['price_caps'],oracle['price_caps'])
        self.assertEqual(got['selected_price_index'],oracle['global']['price_index'])
        self.assertEqual(got['global_charge'],oracle['global']['charge'])
        self.assertEqual(got['rows'],oracle['rows'])
        for row,want in zip(got['price_rows'],oracle['price_rows']):
            self.assertEqual(row,{**want,'entry_charge':want['lambda']*B})
        words=oracle['entry_occurrence_counts'];edges=proof.parent.allowed(kw['texts'],kw['banned'])
        owners={word:{pid for (pid,_,_),value in edges.items() if value==word} for word in words}
        self.assertEqual(got['shared_counts'],[[eid,words[word]] for eid,word in enumerate(kw['old_pool']) if word in owners and len(owners[word])>1])
        for pid,text in kw['texts'].items():
            self.assertEqual(got['unpriced_prefix_schedule'][pid],oracle['price_schedules'][pid][0])
            self.assertEqual(got['unpriced_caps'][pid],oracle['price_caps'][pid][0])
            for start,stream in enumerate(got['count_streams'][pid]):
                h=hashlib.sha256();n=0
                for end in range(start+1,len(text)+1):
                    if (pid,start,end) in edges:
                        h.update(f'[{end},{words[text[start:end]]}]\n'.encode('ascii'));n+=1
                self.assertEqual(stream,{'arcs':n,'sha256':h.hexdigest()})
        A=len(edges);N=sum(map(len,kw['texts'].values()));w=got['work']
        self.assertEqual(w['allowed_endpoints'],A)
        self.assertEqual(w['owner_endpoints']+w['shared_endpoints'],A)
        self.assertEqual(w['shared_endpoints'],sum(count for _,count in got['shared_counts']))
        self.assertEqual(w['forward_arc_candidates'],15*A);self.assertEqual(w['price_residual_evaluations'],15*A)
        self.assertEqual(w['forward_skip_candidates'],15*N);self.assertEqual(w['q_evaluations'],A)
        self.assertEqual(w['unpriced_arc_candidates'],A);self.assertEqual(w['unpriced_skip_candidates'],N)
        self.assertEqual(w['multiplicity_divisions'],15*w['multiplicity_cache_entries'])
        return got

    def test_fixed_prices_full_tiny_dictionary_path_oracle(self):
        rng=random.Random(6617)
        for _ in range(14):
            texts={str(i):''.join(rng.choice('abc') for _ in range(3)) for i in range(2)}
            self.compare(fixture(texts,set(texts.values()),rng=rng),3,True)

    def test_global_shared_overlap_zero_penalties_and_terminal_suffixes(self):
        for texts,bans in (({'p':'aaaa','q':'aaaa'},{'aaaa','aaa'}),
                           ({'p':'abc','q':'bc'},{'abc'}),
                           ({'p':'ababa','q':'cabab'},{'ababa','cabab','aba'}),
                           ({'p':'\u03b1\u03b1\u03b2','q':'\u03b2\u03b1'},set())):
            kw=fixture(texts,bans,seed=['~~']);kw['old_q']=[0]*len(kw['old_q'])
            self.compare(kw,3)
        kw=fixture({'p':'aaaa','q':'aaaa'},{'aaaa'},D=1);got=self.compare(kw,1)
        expected={kw['old_pool'].index('a'):8,kw['old_pool'].index('aa'):6,kw['old_pool'].index('aaa'):4}
        self.assertEqual(dict(got['shared_counts']),expected)

    def test_unpriced_all_entry_vector_matches60_not_owner57(self):
        kw=fixture({'p':'abc','q':'abc'},{'abc'},D=1);kw['old_q']=[20]*len(kw['old_q'])
        got=self.compare(kw,2);q=explicit(kw)
        spec=importlib.util.spec_from_file_location('global66_test60',Path(__file__).resolve().parents[1]/'joint-path-cap-v1/proof.py')
        old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
        oracle=old.certificate(kw['texts'],kw['banned'],q,2,kw['D'])
        self.assertEqual(got['unpriced_prefix_schedule'],oracle['all_schedule_values'])
        self.assertEqual(got['unpriced_caps'],oracle['all_caps'])
        self.assertTrue(all(value>0 for value in got['unpriced_caps'].values()))
        self.assertTrue(all(value==0 for value in got['base57']['owner_caps'].values()))

    def test_capacity_zero_negative_ceiling_and_finite_fixed_grid(self):
        kw=fixture({'p':'abab','q':'abab'},{'abab'},D=3);kw['old_q']=[0]*len(kw['old_q'])
        for B in (0,1,16,256):
            got=self.compare(kw,B)
            self.assertEqual(len(got['rows']),B+1)
            self.assertLess(sum(got['base57']['base']['tightened']['path_numerators'].values()),0)
            self.assertTrue(all(row['integer_lower_bound']==-(-row['numerator']//3) for row in got['price_rows']))
        one=fixture({'p':'aaaa'},{'aaaa'},D=1);self.compare(one,3)
        scaled=copy.deepcopy(one);scaled['D']=3;scaled['old_q']=[3*v for v in one['old_q']]
        self.compare(scaled,3) # floor(lambda/m) is re-evaluated, not assumed to scale

    def test_bans_single_use_and_aliased_generators(self):
        kw=fixture({'p':'ababa','q':'abc'},{'ababa','abc','aba'});expected=caps.check(**kw,capacity=3)
        same=iter(kw['banned'])
        self.assertEqual(caps.check(**(kw|{'banned':same,'expected_old_banned':same}),capacity=3),expected)
        self.assertEqual(caps.check(**(kw|{'banned':iter(kw['banned']),'expected_old_banned':iter(kw['banned'])}),capacity=3),expected)

    def test_authority_invalid_q_capacity_and_missing_shared_identity(self):
        kw=fixture({'p':'abc','q':'abd'},{'abc','abd'})
        for change in ({'expected_source_hashes':{}},{'expected_occurrence_sha256':'0'*64},
                       {'old_q':[True]+kw['old_q'][1:]},{'old_q':[-1]+kw['old_q'][1:]}):
            with self.assertRaises(AssertionError):caps.check(**(kw|change))
        for B in (True,-1,1.0):
            with self.assertRaises(AssertionError):caps.check(**kw,capacity=B)
        kw['old_pool'].remove('ab');kw['old_q']=[0 for pid,text in sorted(kw['texts'].items())
            for start in range(len(text)) for end in range(start+1,len(text)+1) if text[start:end] in kw['old_pool']]
        with self.assertRaisesRegex(AssertionError,'omits an allowed shared'):caps.check(**kw)

    def test_json_roundtrip_multidigit_ids_and_optimized_python(self):
        got=self.compare(fixture({'10':'abacabad','2':'xyzyx'},D=3),16);saved=json.loads(json.dumps(got))
        for key in caps.COMMON+('price_prefix_schedule','unpriced_prefix_schedule'):
            self.assertEqual(got['digests'][key+'_sha256'],caps.digest(saved[key]))
        self.assertEqual(got['digests']['base57_sha256'],caps.digest(caps.scientific57(saved['base57'])))
        changed=copy.deepcopy(saved);changed['shared_counts'].append([999,1])
        self.assertNotEqual(got['digests']['shared_counts_sha256'],caps.digest(changed['shared_counts']))
        proc=subprocess.run([sys.executable,'-O','-B','-c',
            'import caps;caps.check({},set(),[],[],[],[],1,expected_source_hashes={},expected_old_banned=set())'],
            cwd=Path(__file__).resolve().parent,capture_output=True,text=True,timeout=5)
        self.assertNotEqual(proc.returncode,0);self.assertIn('normal assertions required',proc.stderr)

    def test_independent_all_fields_and_both_forward_schedules(self):
        import independent
        for kw,B in ((fixture({'10':'abacabad','2':'xyzyx'},D=3),16),
                     (fixture({'p':'aaaa','q':'aaaa'},{'aaaa'},D=1),1),
                     (fixture({'p':'ab','q':'ab'},{'ab'}),0),
                     (fixture({'p':'\u03b1\u03b1\u03b2','q':'\u03b2\u03b1'}),256)):
            got=caps.check(**kw,capacity=B);saved=json.loads(json.dumps(got))
            checked=independent.check(**kw,capacity=B,
                expected_base57_prefix_schedule=saved['base57']['owner_prefix_schedule'],
                expected_price_prefix_schedule=saved['price_prefix_schedule'],
                expected_unpriced_prefix_schedule=saved['unpriced_prefix_schedule'],
                expected_count_streams=saved['count_streams'],expected_price_caps=saved['price_caps'],
                expected_shared_counts=saved['shared_counts'],expected_price_rows=saved['price_rows'])
            for field in caps.COMMON:
                self.assertEqual(caps.normalized(got[field]),caps.normalized(checked[field]),field)
                self.assertEqual(got['digests'][field+'_sha256'],checked['digests'][field+'_sha256'],field)
            self.assertEqual(got['digests']['base57_sha256'],checked['digests']['base57_sha256'])
            self.assertTrue(checked['production_forward_schedule_checked'])
            self.assertTrue(checked['production_unpriced_forward_checked'])
            self.assertEqual(got['digests']['price_prefix_schedule_sha256'],checked['production_forward_schedule_sha256'])
            self.assertEqual(got['digests']['unpriced_prefix_schedule_sha256'],checked['production_unpriced_forward_sha256'])


if __name__=='__main__':unittest.main()
