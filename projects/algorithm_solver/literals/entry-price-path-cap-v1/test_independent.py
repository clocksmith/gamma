"""Tiny explicit multiplicities/prices/paths; independent supplied checker tests."""
import copy
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest
import independent as audit
import proof


def fixture(texts,banned=(),seed=(),D=7,rng=None):
    banned=set(banned);rng=rng or random.Random(6307);edges=proof.parent.allowed(texts,banned)
    owners={w:{pid for (pid,i,j),v in edges.items() if v==w} for w in set(edges.values())}
    alphabet=sorted(set(''.join(texts.values()))|{'~'})
    pool=sorted(set(alphabet)|set(seed)|{w for w,ps in owners.items() if len(ps)>=2})
    q=[rng.randrange(40) for pid,text in sorted(texts.items()) for i in range(len(text))
       for j in range(i+1,len(text)+1) if text[i:j] in pool]
    return dict(texts=texts,banned=banned,old_pool=pool,old_q=q,seed=list(seed),alphabet=alphabet,D=D,
        expected_source_hashes={pid:hashlib.sha256(text.encode()).hexdigest() for pid,text in texts.items()},expected_old_banned=banned)


def explicit(kw):
    texts=kw['texts'];D=kw['D'];values=iter(kw['old_q']);old={}
    for pid,text in sorted(texts.items()):
        for start in range(len(text)):
            for end in range(start+1,len(text)+1):
                if text[start:end] in kw['old_pool']:old[pid,start,end]=next(values)
    d={}
    for pid,text in texts.items():
        vector=[None]*len(text)+[0]
        for start in range(len(text)-1,-1,-1):
            vector[start]=min((9 if end-start==1 else -1)*D+old[pid,start,end]+vector[end]
                             for end in range(start+1,len(text)+1) if (pid,start,end) in old)
        d[pid]=vector
    edges=proof.parent.allowed(texts,kw['banned'])
    q={e:max(0,d[e[0]][e[1]]-d[e[0]][e[2]]-(9 if e[2]-e[1]==1 else -1)*D) for e in edges}
    return q,d


def forward_and_streams(kw,q,prices):
    texts=kw['texts'];edges=proof.parent.allowed(texts,kw['banned'])
    owners={w:{pid for (pid,i,j),v in edges.items() if v==w} for w in set(edges.values())}
    counts={w:sum(v==w for v in edges.values()) for w in owners};schedules={};streams={}
    for pid,text in texts.items():
        schedules[pid]=[];streams[pid]=[]
        for price in prices:
            vec=[0]
            for end in range(1,len(text)+1):
                offered=[vec[-1]]
                for start in range(end):
                    w=edges.get((pid,start,end))
                    if w is not None and owners[w]=={pid}:offered.append(vec[start]+max(0,q[pid,start,end]-price//counts[w]))
                vec.append(max(offered))
            schedules[pid].append(vec)
        for start in range(len(text)):
            records=[]
            for end in range(start+1,len(text)+1):
                w=edges.get((pid,start,end))
                if w is not None and owners[w]=={pid}:records.append([end,counts[w]])
            raw=''.join(json.dumps(row,separators=(',',':'))+'\n' for row in records).encode('ascii')
            streams[pid].append({'arcs':len(records),'sha256':hashlib.sha256(raw).hexdigest()})
    return schedules,streams


class IndependentTests(unittest.TestCase):
    def compare(self,kw,B=3):
        q,d=explicit(kw);prices=[0]+[kw['D']*2**r for r in range(14)]
        oracle=proof.certificate(kw['texts'],kw['banned'],q,prices,B,kw['D'])
        forward,streams=forward_and_streams(kw,q,prices)
        result=audit.check(**kw,capacity=B,expected_base57_prefix_schedule=oracle['base57']['owner_schedule_values'],
            expected_price_prefix_schedule=forward,expected_count_streams=streams,
            expected_price_caps={pid:[oracle['price_caps'][pid][price] for price in prices] for pid in kw['texts']})
        self.assertEqual(result['count_streams'],streams);self.assertEqual(result['price_caps'],{pid:[v[p] for p in prices] for pid,v in oracle['price_caps'].items()})
        for key in ('affine_envelopes','priced_prefixes','one_owner_prefix','marginal_choices','shared_prefix'):
            expected=oracle['base57'][key] if key=='shared_prefix' else oracle[key]
            self.assertEqual(audit.normalized(result[key]),audit.normalized(expected),key)
        for row,expected in zip(result['rows'],oracle['rows']):self.assertEqual(row,{key:expected[key] for key in row})
        self.assertEqual(result['base57']['base']['digests']['potentials_sha256'],audit.digest(d))
        self.assertEqual(result['work']['production_forward_positions_checked'],15*sum(map(len,kw['texts'].values())))
        self.assertEqual(result['production_forward_schedule_sha256'],audit.digest(forward))
        # The baseline is the unchanged scientific proof, not another q family.
        self.assertEqual(result['digests']['base57_sha256'],audit.digest(audit.scientific57(result['base57'])))
        serialized=json.loads(json.dumps(result,sort_keys=True))
        self.assertEqual(audit.digest(audit.scientific(result)),audit.digest(audit.scientific(serialized)))
        self.assertEqual(result['digests'],serialized['digests'])
        return result,forward,streams

    def test_z_all_lengths_overlaps_terminals_and_unicode(self):
        for text in ('aaaa','aba','a','aaabX','\U00010400a\U00010400a','a\n~a'):
            for start in range(len(text)):
                counts,_=audit.z_counts(list(map(ord,text)),start)
                for length in range(1,len(text)-start+1):
                    word=text[start:start+length]
                    self.assertEqual(counts[length],sum(text.startswith(word,i) for i in range(len(text))))
        for bad in ([0,-1],[True],[1.5]):
            with self.assertRaises(AssertionError):audit.z_counts(bad,0)

    def test_complete_prices_tiny_random_and_finite_capacities(self):
        rng=random.Random(6315)
        for _ in range(10):
            texts={str(i):''.join(rng.choice('abc') for _ in range(3)) for i in range(2)}
            kw=fixture(texts,set(texts.values()),rng=rng)
            self.compare(kw,B=3)
        for B in (0,1,4,8):self.compare(fixture({'p':'aaaa','q':'aa','r':'ab'},{'aaaa','ab'}),B)

    def test_bans_absent_seed_and_zero_old_penalties(self):
        kw=fixture({'0':'abcxabc','1':'abcyabc'},{'abc','abcxabc','abcyabc'},seed=['cx','~~'])
        self.compare(kw,4)
        kw=fixture({'p':'aaaa','q':'bb'},{'aaaa','bb'},seed=['aaa','~~']);kw['old_q']=[0]*len(kw['old_q'])
        result,_,_=self.compare(kw,1)
        self.assertEqual(result['price_caps']['q'][0],0)
        self.assertGreater(result['work']['old_owned_occurrence_counts_checked'],0)
        for same in (False,True):
            supplied=dict(kw);supplied['banned']=iter(kw['banned'])
            supplied['expected_old_banned']=supplied['banned'] if same else iter(kw['expected_old_banned'])
            other=audit.check(**supplied,capacity=1)
            self.assertEqual(audit.digest(audit.scientific(result)),audit.digest(audit.scientific(other)))

    def test_corrupt_intermediate_forward_counts_and_bool_caps(self):
        kw=fixture({'p':'aaaa','q':'bb'},{'aaaa','bb'},seed=['aaa'])
        got,forward,streams=self.compare(kw,3)
        bad=copy.deepcopy(forward);bad['p'][1][1]+=1
        with self.assertRaises(AssertionError):audit.check(**kw,capacity=3,expected_price_prefix_schedule=bad)
        bad=copy.deepcopy(streams);bad['p'][0]['sha256']='0'*64
        with self.assertRaises(AssertionError):audit.check(**kw,capacity=3,expected_count_streams=bad)
        bad=copy.deepcopy(got['price_caps']);bad['p'][0]=True
        with self.assertRaises(AssertionError):audit.check(**kw,capacity=3,expected_price_caps=bad)
        with self.assertRaises(AssertionError):audit.check(**kw,capacity=3,expected_occurrence_sha256='0'*64)

    def test_missing_shared_entry_q_corruption_and_optimized_python(self):
        kw=fixture({'p':'abx','q':'aby'},{'abx','aby'})
        broken=copy.deepcopy(kw);at=broken['old_pool'].index('ab');broken['old_pool'].pop(at)
        broken['old_q']=[0 for pid,text in sorted(broken['texts'].items()) for i in range(len(text))
                         for j in range(i+1,len(text)+1) if text[i:j] in broken['old_pool']]
        with self.assertRaises(AssertionError):audit.check(**broken)
        for value in (-1,True):
            broken=copy.deepcopy(kw);broken['old_q'][0]=value
            with self.assertRaises(AssertionError):audit.check(**broken)
        for script in ('import independent;independent.z_counts([97],0)',
                       'import independent;independent.check({},set(),[],[],[],[],1,expected_source_hashes={},expected_old_banned=set())'):
            proc=subprocess.run([sys.executable,'-O','-B','-c',script],cwd=Path(__file__).resolve().parent,capture_output=True,timeout=5)
            self.assertNotEqual(proc.returncode,0);self.assertIn(b'normal assertions required',proc.stderr)


if __name__=='__main__':unittest.main()
