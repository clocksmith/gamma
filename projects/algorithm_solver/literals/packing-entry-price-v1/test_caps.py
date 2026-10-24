"""Invented q53 replay against the independent tiny packing theorem oracle."""
import copy
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest
import caps
import proof


def fixture(texts,banned=(),seed=(),D=7,rng=None):
    banned=set(banned);rng=rng or random.Random(7107);owners={}
    for pid,text in texts.items():
        for i in range(len(text)):
            for j in range(i+1,len(text)+1):
                word=text[i:j]
                if word not in banned:owners.setdefault(word,set()).add(pid)
    alphabet=sorted(set(''.join(texts.values()))|{'~'})
    pool=sorted(set(alphabet)|set(seed)|{word for word,pids in owners.items() if len(pids)>1})
    q=[rng.randrange(40) for pid,text in sorted(texts.items()) for i in range(len(text))
       for j in range(i+1,len(text)+1) if text[i:j] in pool]
    return dict(texts=texts,banned=banned,old_pool=pool,old_q=q,seed=list(seed),alphabet=alphabet,D=D,
        expected_source_hashes={pid:hashlib.sha256(text.encode()).hexdigest() for pid,text in texts.items()},expected_old_banned=banned)


def explicit(kw):
    """Original ordered occurrence DP, then every explicit q53 occurrence."""
    texts,D=kw['texts'],kw['D'];values=iter(kw['old_q'])
    old={(pid,i,j):next(values) for pid,text in sorted(texts.items()) for i in range(len(text))
         for j in range(i+1,len(text)+1) if text[i:j] in kw['old_pool']}
    ds={}
    for pid,text in texts.items():
        d=[None]*len(text)+[0]
        for i in range(len(text)-1,-1,-1):
            d[i]=min(D*(9 if j-i==1 else -1)+old[pid,i,j]+d[j]
                     for j in range(i+1,len(text)+1) if (pid,i,j) in old)
        ds[pid]=d
    q={(pid,i,j):max(0,ds[pid][i]-ds[pid][j]-D*(9 if j-i==1 else -1))
       for pid,text in texts.items() for i in range(len(text)) for j in range(i+1,len(text)+1)
       if text[i:j] not in kw['banned']}
    return q,ds


class CapsTests(unittest.TestCase):
    def compare(self,kw,B=3):
        got=caps.check(**kw,capacity=B);q,ds=explicit(kw)
        prices=[0]+[kw['D']*2**i for i in range(14)]
        oracle=proof.certificate(kw['texts'],kw['banned'],q,prices,B,kw['D'])
        self.assertEqual(got['base63'],caps.prior.check(**kw,capacity=B))
        self.assertEqual(got['lambda_family'],prices)
        for field in ('affine_envelopes','priced_prefixes','one_owner_prefix','marginal_choices'):
            self.assertEqual(got[field],oracle['owner_'+field],field)
        self.assertEqual(got['shared_prefix'],oracle['base57']['shared_prefix'])
        self.assertEqual(got['price_caps'],oracle['owner_price_caps'])
        self.assertEqual(got['price_prefix_schedule'],oracle['owner_price_schedules'])
        records=[]
        for pid,text in kw['texts'].items():
            for start,stream in enumerate(got['count_streams'][pid]):
                h=hashlib.sha256();count=0
                for end in range(start+1,len(text)+1):
                    word=text[start:end]
                    if oracle['base57']['support'].get(word)!=pid:continue
                    m=oracle['occurrence_counts'][word];n=oracle['packing_counts'][word]
                    records.append((m,n));h.update(f'[{end},{m},{n}]\n'.encode('ascii'));count+=1
                self.assertEqual(stream,{'arcs':count,'sha256':h.hexdigest()})
        for row,want in zip(got['rows'],oracle['owner_rows']):
            self.assertEqual(row,{key:want[key] for key in row})
        diag={'owner_endpoints':len(records),'reduced_endpoints':sum(n<m for m,n in records),
              'max_m':max((m for m,n in records),default=0),'max_n':max((n for m,n in records),default=0),
              'sum_m_minus_n':sum(m-n for m,n in records),
              'reduced_share':sum(n<m for m,n in records)/len(records) if records else None}
        self.assertEqual(got['packing_diagnostics'],diag)
        w=got['work'];A=len(records);N=sum(map(len,kw['texts'].values()))
        for key in ('q_evaluations','packing_divisions','count_stream_records','allowed_owner_endpoints'):
            self.assertEqual(w[key],A,key)
        for key in ('price_residual_evaluations','pointwise_residual_checks','forward_arc_candidates'):
            self.assertEqual(w[key],15*A,key)
        self.assertEqual(w['forward_skip_candidates'],15*N)
        self.assertEqual(w['forward_vector_positions_checked'],15*(N+len(kw['texts'])))
        self.assertEqual(w['packing_quotient_divisions'],15*len({n for m,n in records}))
        self.assertEqual(w['packing_cache_entries'],len({n for m,n in records}))
        return got

    def test_actual_q53_full_oracle(self):
        rng=random.Random(7117)
        for _ in range(12):
            texts={str(i):''.join(rng.choice('abc') for _ in range(3)) for i in range(2)}
            self.compare(fixture(texts,set(texts.values()),rng=rng),3)

    def test_within_group_packing_changes_and_bans(self):
        kw=fixture({'p':'abcabcabc'},{'abcabcabc','bcab'},D=1)
        got=self.compare(kw,16);index=caps.parent.full.Index(kw['texts'],kw['banned'])
        changed=[]
        for g in index.groups:
            m=g['hi']-g['lo'];ns={min(m,9//ell) for ell in range(g['first'],g['last']+1)
                                if ell not in g['excluded_lengths']}
            if len(ns)>1:changed.append(ns)
        self.assertTrue(changed,'fixture must cross n boundary inside a single constant-m group')
        self.assertGreater(got['packing_diagnostics']['reduced_endpoints'],0)
        self.assertGreater(got['work']['banned_owner_endpoints'],0)

    def test_zero_weights_paid_singletons_absent_seed_unicode(self):
        kw=fixture({'p':'aaaa'},{'aaaa'},seed=['aaa','~~'],D=1)
        kw['old_q']=[0]*len(kw['old_q']);got=self.compare(kw,256)
        self.assertEqual(got['count_streams']['p'][0]['arcs'],3)
        self.assertEqual(got['packing_diagnostics']['max_m'],4)
        self.assertTrue(all(value==0 for value in got['price_prefix_schedule']['p'][-1]))
        self.compare(fixture({'10':'\u03b1\u03b1\u03b2','2':'\u03b2\u03b1'},{'\u03b1\u03b1\u03b2','\u03b2\u03b1'}),16)
        # Original53 requires all alphabet singletons in its unbanned old pool.
        with self.assertRaisesRegex(AssertionError,'old path edge may be banned'):
            caps.check(**fixture({'p':'aa'},{'a'}),capacity=1)

    def test_no_owner_and_zero_capacity(self):
        kw=fixture({'p':'ab','q':'ab'},{'ab'})
        for B in (0,1,16,256):
            got=self.compare(kw,B)
            self.assertEqual(got['one_owner_prefix'],[0])
            self.assertEqual(got['packing_diagnostics'],dict(owner_endpoints=0,reduced_endpoints=0,
                max_m=0,max_n=0,sum_m_minus_n=0,reduced_share=None))
        self.compare(fixture({'p':'aaaa'},{'aaaa'}),0)

    def test_authority_missing_shared_and_strict_types(self):
        kw=fixture({'p':'abc','q':'abd'},{'abc','abd'})
        for change in ({'expected_source_hashes':{}},{'expected_occurrence_sha256':'0'*64},
                       {'expected_old_banned':{'wrong'}},{'old_q':[True]+kw['old_q'][1:]},
                       {'old_q':[-1]+kw['old_q'][1:]}):
            with self.assertRaises(AssertionError):caps.check(**(kw|change))
        for B in (True,-1,1.0):
            with self.assertRaises(AssertionError):caps.check(**kw,capacity=B)
        kw['old_pool'].remove('ab');kw['old_q']=[0 for pid,text in sorted(kw['texts'].items())
            for start in range(len(text)) for end in range(start+1,len(text)+1) if text[start:end] in kw['old_pool']]
        with self.assertRaisesRegex(AssertionError,'omits an allowed shared'):caps.check(**kw)

    def test_ban_generators_and_no_mutation(self):
        kw=fixture({'p':'ababa','q':'abc'},{'ababa','abc','aba'})
        original=copy.deepcopy(kw);expected=caps.check(**kw,capacity=3);self.assertEqual(kw,original)
        separate=kw|{'banned':iter(kw['banned']),'expected_old_banned':iter(kw['expected_old_banned'])}
        self.assertEqual(caps.check(**separate,capacity=3),expected)
        same=iter(kw['banned'])
        self.assertEqual(caps.check(**(kw|{'banned':same,'expected_old_banned':same}),capacity=3),expected)

    def test_normalization_and_optimized_refusal(self):
        got=self.compare(fixture({'10':'abacabad','2':'xyzyx'},D=3),16)
        saved=json.loads(json.dumps(got))
        self.assertEqual(caps.digest(caps.scientific(got)),caps.digest(caps.scientific(saved)))
        for key in caps.COMMON+('price_prefix_schedule',):
            self.assertEqual(got['digests'][key+'_sha256'],caps.digest(saved[key]))
        values={i:i*i for i in range(16)}
        self.assertEqual(caps.digest(values),caps.digest(json.loads(json.dumps(values))))
        for bad in ({1:2,'1':3},{True:1},{'x':float('nan')},{'x':float('inf')},{'x':set()}):
            with self.assertRaises(AssertionError):caps.normalized(bad)
        proc=subprocess.run([sys.executable,'-O','-B','-c',
            'import caps;caps.check({},set(),[],[],[],[],1,expected_source_hashes={},expected_old_banned=set())'],
            cwd=Path(__file__).resolve().parent,capture_output=True,text=True,timeout=5)
        self.assertNotEqual(proc.returncode,0);self.assertIn('normal assertions required',proc.stderr)

    def test_independent_actual_json_full_science_and_all_vectors(self):
        import independent
        cases=[(fixture({'10':'abcabcabc','2':'xyzyx'},D=3),16),
               (fixture({'p':'aaaa'},{'aaaa'},seed=['aaa','~~'],D=1),1),
               (fixture({'p':'ab','q':'ab'},{'ab'}),0),
               (fixture({'p':'\u03b1\u03b1\u03b2','q':'\u03b2\u03b1'},{'\u03b1\u03b1\u03b2','\u03b2\u03b1'}),256)]
        for kw,B in cases:
            got=caps.check(**kw,capacity=B);saved=json.loads(json.dumps(got))
            checked=independent.check(**kw,capacity=B,expected_base63=saved['base63'],
                expected_price_prefix_schedule=saved['price_prefix_schedule'],
                expected_count_streams=saved['count_streams'],expected_price_caps=saved['price_caps'],
                expected_packing_diagnostics=saved['packing_diagnostics'])
            self.assertTrue(checked['production_forward_schedule_checked'])
            self.assertEqual(checked['production_forward_schedule_sha256'],got['digests']['price_prefix_schedule_sha256'])
            self.assertEqual(caps.normalized(caps.scientific(got)),caps.normalized(independent.scientific(checked)))
            for field in caps.COMMON:
                self.assertEqual(got['digests'][field+'_sha256'],checked['digests'][field+'_sha256'])
            self.assertEqual(got['digests']['base63_sha256'],checked['digests']['base63_sha256'])


if __name__=='__main__':unittest.main()
