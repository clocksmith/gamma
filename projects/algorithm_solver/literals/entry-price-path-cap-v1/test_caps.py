"""Tiny invented production geometry, count, schedule and allocation checks."""
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
import test_proof


def fixture(texts,banned=(),seed=(),D=7,rng=None):
    banned=set(banned);rng=rng or random.Random(6307);owners={}
    for (pid,i,j),word in proof.parent.allowed(texts,banned).items():owners.setdefault(word,set()).add(pid)
    alphabet=sorted(set(''.join(texts.values()))|{'~'})
    pool=sorted(set(alphabet)|set(seed)|{word for word,pids in owners.items() if len(pids)>1})
    q=[rng.randrange(40) for pid,text in sorted(texts.items()) for i in range(len(text))
       for j in range(i+1,len(text)+1) if text[i:j] in pool]
    return dict(texts=texts,banned=banned,old_pool=pool,old_q=q,seed=list(seed),alphabet=alphabet,D=D,
        expected_source_hashes={pid:hashlib.sha256(text.encode()).hexdigest() for pid,text in texts.items()},expected_old_banned=banned)


def explicit(kw):
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
    q={edge:max(0,ds[edge[0]][edge[1]]-ds[edge[0]][edge[2]]-D*(9 if edge[2]-edge[1]==1 else -1))
       for edge in proof.parent.allowed(texts,kw['banned'])}
    return q,ds


class CapsTests(unittest.TestCase):
    def compare(self,kw,B=3,exhaustive=False):
        got=caps.check(**kw,capacity=B);q,ds=explicit(kw);prices=[0]+[kw['D']*2**i for i in range(14)]
        oracle=(test_proof.ProofTests().check(kw['texts'],kw['banned'],q,prices,B,kw['D'])[0] if exhaustive else
                proof.certificate(kw['texts'],kw['banned'],q,prices,B,kw['D']))
        self.assertEqual(got['lambda_family'],prices)
        for field in ('affine_envelopes','priced_prefixes','one_owner_prefix','marginal_choices','shared_prefix'):
            expected=oracle['base57']['shared_prefix'] if field=='shared_prefix' else oracle[field]
            self.assertEqual(got[field],expected,field)
        for pid,text in kw['texts'].items():
            self.assertEqual(got['price_caps'][pid],[oracle['price_caps'][pid][price] for price in prices])
            self.assertEqual(got['price_prefix_schedule'][pid],[oracle['price_schedules'][pid][price] for price in prices])
            for start,stream in enumerate(got['count_streams'][pid]):
                h=hashlib.sha256();n=0
                for end in range(start+1,len(text)+1):
                    word=text[start:end]
                    if word in oracle['entry_occurrence_counts']:
                        m=oracle['entry_occurrence_counts'][word];h.update(f'[{end},{m}]\n'.encode('ascii'));n+=1
                self.assertEqual(stream,{'arcs':n,'sha256':h.hexdigest()})
        for row,want in zip(got['rows'],oracle['rows']):
            for key in ('k','charge','one_owner_slots','shared_slots','numerator','integer_lower_bound'):
                self.assertEqual(row[key],want[key],key)
        self.assertEqual(got['work']['q_evaluations'],sum(row['arcs'] for rows in got['count_streams'].values() for row in rows))
        self.assertEqual(got['work']['price_residual_evaluations'],15*got['work']['q_evaluations'])
        self.assertEqual(got['work']['forward_skip_candidates'],15*sum(map(len,kw['texts'].values())))
        self.assertEqual(got['work']['multiplicity_divisions'],15*got['work']['multiplicity_cache_entries'])
        return got

    def test_fixed15_prices_full_tiny_oracle(self):
        rng=random.Random(6317)
        for _ in range(14):
            texts={str(i):''.join(rng.choice('abc') for _ in range(3)) for i in range(2)}
            self.compare(fixture(texts,set(texts.values()),rng=rng),3,True)

    def test_laminar_depth_partitions_all_counts_and_terminal_prefixes(self):
        for texts,banned in (({'p':'aaaa'},{'aa','aaaa'}),({'p':'abc','q':'bc'},set()),
                             ({'p':'aba','q':'aba'},{'aba'}),({'p':'\u03b1\u03b1\u03b2','q':'\u03b2\u03b1'},set()),
                             ({'p':'a'},{'a'})):
            index=caps.parent.full.Index(texts,banned);mapping=caps.DepthMap(index)
            for pid,text in texts.items():
                for start in range(len(text)):
                    depths=[]
                    for gid in mapping.chain(pid,start):
                        g=index.groups[gid]
                        for length in range(g['first'],g['last']+1):
                            depths.append(length);word=text[start:start+length]
                            m=sum(source.startswith(word,j) for source in texts.values() for j in range(len(source)))
                            self.assertEqual(m,g['hi']-g['lo'])
                            self.assertEqual(length in g['excluded_lengths'],word in banned)
                    self.assertEqual(depths,list(range(1,len(text)-start+1)))

    def test_repeated_zero_occurrences_low_rank_arcs_and_absent_seed(self):
        kw=fixture({'p':'aaaa'},{'aaaa'},seed=['aaa','~~'],D=1);kw['old_q']=[4,10,4,10,4,4]
        got=self.compare(kw,1)
        self.assertEqual(got['price_caps']['p'][0],31)
        self.assertGreater(got['price_caps']['p'][0],got['base57']['owner_top_entries']['p'][0][0])
        zero=fixture({'p':'aaaa'},{'aaaa'},D=1);zero['old_q']=[0]*len(zero['old_q'])
        got=self.compare(zero,256)
        self.assertEqual(got['count_streams']['p'][0]['arcs'],3)
        self.assertTrue(all(v==0 for v in got['price_prefix_schedule']['p'][-1]))
        self.compare(fixture({'p':'\u03b1\u03b1\u03b2','q':'\u03b2\u03b1'},{'\u03b1\u03b1\u03b2','\u03b2\u03b1'}),3)

    def test_no_owner_capacity_zero_and_exact_scaling(self):
        kw=fixture({'p':'ab','q':'ab'},{'ab'})
        for B in (0,1,8):
            got=self.compare(kw,B);self.assertEqual(got['one_owner_prefix'],[0])
            self.assertTrue(all(row['arcs']==0 for rows in got['count_streams'].values() for row in rows))
        kw=fixture({'p':'ababa'},{'ababa'},D=1)
        one=self.compare(kw,3);scaled=copy.deepcopy(kw);scaled['D']=3;scaled['old_q']=[3*v for v in kw['old_q']]
        three=self.compare(scaled,3)
        # Floor(lambda/m) does not commute with scaling when lambda/m is not
        # integral; use exact oracle comparison, never infer scaled cap equality.
        self.assertEqual(three['lambda_family'],[3*v for v in one['lambda_family']])

    def test_corrupt_structural_parent_width_terminal_and_authority(self):
        index=caps.parent.full.Index({'p':'aaaa'},set())
        for change in ('width','first','terminal','remaining'):
            bad=copy.deepcopy(index)
            if change=='width':bad.groups[0]['hi']=len(bad.positions)+1
            elif change=='first':bad.groups[0]['first']+=1
            elif change=='terminal':bad.groups[-1]['last']+=1;bad.groups[-1]['multiplicity']+=1
            else:bad.remaining[0]+=1
            with self.assertRaises(AssertionError):caps.DepthMap(bad)
        kw=fixture({'p':'abc','q':'abd'},{'abc','abd'})
        for change in ({'expected_source_hashes':{}},{'expected_occurrence_sha256':'0'*64},
                       {'old_q':[True]+kw['old_q'][1:]},{'old_q':[-1]+kw['old_q'][1:]}):
            with self.assertRaises(AssertionError):caps.check(**(kw|change))
        kw['old_pool'].remove('ab');kw['old_q']=[0 for pid,text in sorted(kw['texts'].items())
            for start in range(len(text)) for end in range(start+1,len(text)+1) if text[start:end] in kw['old_pool']]
        with self.assertRaisesRegex(AssertionError,'omits an allowed shared'):caps.check(**kw)

    def test_integer_key_json_roundtrip_and_optimized_python(self):
        got=self.compare(fixture({'10':'abacabad','2':'xyzyx'},D=3),16)
        restored=json.loads(json.dumps(got))
        for key in caps.COMMON+('price_prefix_schedule',):
            self.assertEqual(caps.digest(got[key]),caps.digest(restored[key]))
            self.assertEqual(got['digests'][key+'_sha256'],caps.digest(restored[key]))
        self.assertEqual(caps.digest(caps.scientific57(got['base57'])),caps.digest(caps.scientific57(restored['base57'])))
        values={i:i*i for i in range(15)}
        self.assertEqual(caps.digest(values),caps.digest(json.loads(json.dumps(values))))
        self.assertNotEqual(caps.digest(values),caps.digest(values|{12:1}))
        proc=subprocess.run([sys.executable,'-O','-B','-c',
            'import caps;caps.check({},set(),[],[],[],[],1,expected_source_hashes={},expected_old_banned=set())'],
            cwd=Path(__file__).resolve().parent,capture_output=True,text=True,timeout=5)
        self.assertNotEqual(proc.returncode,0);self.assertIn('normal assertions required',proc.stderr)

    def test_one_shot_ban_and_authority_iterables(self):
        kw=fixture({'p':'ababa','q':'abc'},{'ababa','abc','aba'})
        expected=caps.check(**kw,capacity=3)
        separate=kw|{'banned':(word for word in kw['banned']),
                     'expected_old_banned':(word for word in kw['expected_old_banned'])}
        self.assertEqual(caps.check(**separate,capacity=3),expected)
        same=(word for word in kw['banned'])
        self.assertEqual(caps.check(**(kw|{'banned':same,'expected_old_banned':same}),capacity=3),expected)

    def test_independent_full_science_and_forward_recurrence_agreement(self):
        import independent
        cases=[(fixture({'10':'abacabad','2':'xyzyx'},D=3),16),
               (fixture({'p':'aaaa'},{'aaaa'},seed=['aaa','~~'],D=1),1),
               (fixture({'p':'ab','q':'ab'},{'ab'}),0),
               (fixture({'p':'\u03b1\u03b1\u03b2','q':'\u03b2\u03b1'},{'\u03b1\u03b1\u03b2','\u03b2\u03b1'}),256)]
        for kw,B in cases:
            got=caps.check(**kw,capacity=B)
            # Replay the actual JSON transport, including inherited integer keys.
            saved=json.loads(json.dumps(got))
            checked=independent.check(**kw,capacity=B,
                expected_base57_prefix_schedule=saved['base57']['owner_prefix_schedule'],
                expected_price_prefix_schedule=saved['price_prefix_schedule'],
                expected_count_streams=saved['count_streams'],expected_price_caps=saved['price_caps'])
            self.assertTrue(checked['production_forward_schedule_checked'])
            self.assertEqual(checked['production_forward_schedule_sha256'],got['digests']['price_prefix_schedule_sha256'])
            for field in caps.COMMON:
                self.assertEqual(caps.normalized(got[field]),caps.normalized(checked[field]),field)
                self.assertEqual(got['digests'][field+'_sha256'],checked['digests'][field+'_sha256'],field)
            self.assertEqual(got['digests']['base57_sha256'],checked['digests']['base57_sha256'])


if __name__=='__main__':unittest.main()
