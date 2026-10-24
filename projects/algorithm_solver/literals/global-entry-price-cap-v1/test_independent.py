"""Supplied q53 oracles/global-count corruption; no private inputs."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest
import independent as audit
import proof


def fixture(texts,banned=(),seed=(),D=7,rng=None):
    banned=set(banned);rng=rng or random.Random(6607);edges=proof.parent.allowed(texts,banned)
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


def count_streams(kw):
    edges=proof.parent.allowed(kw['texts'],kw['banned'])
    counts={word:sum(v==word for v in edges.values()) for word in set(edges.values())};streams={}
    for pid,text in kw['texts'].items():
        streams[pid]=[]
        for start in range(len(text)):
            rows=[[end,counts[edges[pid,start,end]]] for end in range(start+1,len(text)+1) if (pid,start,end) in edges]
            raw=''.join(json.dumps(row,separators=(',',':'))+'\n' for row in rows).encode('ascii')
            streams[pid].append({'arcs':len(rows),'sha256':hashlib.sha256(raw).hexdigest()})
    owners={w:{pid for (pid,i,j),word in edges.items() if word==w} for w in counts}
    shared=[[eid,counts[w]] for eid,w in enumerate(kw['old_pool']) if len(owners.get(w,set()))>=2]
    return streams,shared


def all_schedules(intervals):
    yield []
    ordered=sorted(intervals)
    for index,first in enumerate(ordered):
        for tail in all_schedules([edge for edge in ordered[index+1:] if edge[0]>=first[1]]):yield [first]+tail


class IndependentTests(unittest.TestCase):
    def compare(self,kw,B=3,exhaust=False):
        q,d=explicit(kw);prices=[0]+[kw['D']*2**r for r in range(14)]
        oracle=proof.certificate(kw['texts'],kw['banned'],q,prices,B,kw['D'])
        forward=oracle['price_schedules'];unpriced={pid:vectors[0] for pid,vectors in forward.items()}
        streams,shared=count_streams(kw);rows=[dict(row,entry_charge=row['lambda']*B) for row in oracle['price_rows']]
        result=audit.check(**kw,capacity=B,expected_base57_prefix_schedule=oracle['base57']['owner_schedule_values'],
            expected_price_prefix_schedule=forward,expected_unpriced_prefix_schedule=unpriced,
            expected_count_streams=streams,expected_price_caps=oracle['price_caps'],expected_shared_counts=shared,expected_price_rows=rows)
        for key in ('price_caps','rows'):self.assertEqual(result[key],oracle[key])
        self.assertEqual(result['price_rows'],rows);self.assertEqual(result['count_streams'],streams)
        self.assertEqual(result['shared_counts'],shared);self.assertEqual(result['selected_price_index'],oracle['global']['price_index'])
        self.assertEqual(result['global_charge'],oracle['global']['charge'])
        self.assertEqual(result['unpriced_caps'],{pid:vec[-1] for pid,vec in unpriced.items()})
        for pid,vectors in result['price_suffix_schedule'].items():self.assertEqual(vectors[0],result['unpriced_suffix_schedule'][pid])
        self.assertEqual(result['base57']['base']['digests']['potentials_sha256'],audit.digest(d))
        for row,old,delta in zip(result['rows'],result['base57']['rows'],result['deltas_vs57']):
            self.assertEqual(delta,{'k':row['k'],'charge_reduction':old['charge']-row['charge'],
                'integer_bound_gain':row['integer_lower_bound']-old['integer_lower_bound']})
        N=sum(map(len,kw['texts'].values()));A=len(q);work=result['work']
        self.assertEqual(work['production_forward_positions_checked'],15*N)
        self.assertEqual(work['unpriced_production_forward_positions_checked'],N)
        for key in ('production_forward_candidates','backward_candidates','price_residual_evaluations','multiplicity_divisions'):self.assertEqual(work[key],15*A,key)
        for key in ('unpriced_backward_candidates','unpriced_production_forward_candidates','count_records','q_evaluations'):self.assertEqual(work[key],A,key)
        self.assertEqual(work['shared_occurrences']+work['one_owner_occurrences'],A)
        self.assertEqual(work['shared_occurrences'],sum(count for eid,count in shared))
        self.assertEqual(result['production_forward_schedule_sha256'],audit.digest(forward))
        self.assertEqual(result['production_unpriced_forward_sha256'],audit.digest(unpriced))
        serialized=json.loads(json.dumps(result,sort_keys=True))
        self.assertEqual(audit.digest(audit.scientific(result)),audit.digest(audit.scientific(serialized)))
        self.assertEqual(result['digests'],serialized['digests'])
        if exhaust:
            edges=proof.parent.allowed(kw['texts'],kw['banned']);counts=oracle['entry_occurrence_counts']
            for pid,text in kw['texts'].items():
                choices=list(all_schedules([(i,j,w,q[pid,i,j]) for (source,i,j),w in edges.items() if source==pid]))
                for index,price in enumerate(prices):
                    exact=max(sum(max(v-price//counts[word],0) for _,_,word,v in choice) for choice in choices)
                    self.assertEqual(result['price_caps'][pid][index],exact)
        return result,forward,streams,shared,rows

    def test_q53_prices_random_tiny_and_shared_owner_mix(self):
        rng=random.Random(6615)
        for _ in range(12):
            texts={str(i):''.join(rng.choice('abc') for _ in range(3)) for i in range(2)}
            self.compare(fixture(texts,set(texts.values()),rng=rng),3,True)
        for B in (0,1,4,12):self.compare(fixture({'10':'aaaa','2':'aa','3':'ab'},{'aaaa','ab'}),B,True)

    def test_identical_global_counts_bans_and_unpriced60(self):
        kw=fixture({'10':'aaabaaab','2':'aaabaaab'},{'aaabaaab','aaa'},seed=['~~'])
        result,_,_,shared,_=self.compare(kw,1)
        self.assertEqual(dict(shared)[kw['old_pool'].index('aa')],8)
        self.assertEqual(dict(shared)[kw['old_pool'].index('b')],4)
        self.assertEqual(result['work']['one_owner_occurrences'],0)
        spec=importlib.util.spec_from_file_location('global66_check60',Path(__file__).resolve().parents[1]/'joint-path-cap-v1/proof.py')
        joint=importlib.util.module_from_spec(spec);spec.loader.exec_module(joint)
        q,_=explicit(kw);oracle=joint.certificate(kw['texts'],kw['banned'],q,1,kw['D'])
        self.assertEqual(result['unpriced_caps'],oracle['all_caps'])
        self.assertEqual(result['base57']['base']['tightened']['path_numerators'],{pid:v[0] for pid,v in oracle['distances'].items()})

    def test_zero_old_q_absent_seed_aliased_bans_and_astral_prefix(self):
        kw=fixture({'p':'aaaa','q':'bb'},{'aaaa','bb'},seed=['aaa','~~']);kw['old_q']=[0]*len(kw['old_q'])
        result,_,_,_,_=self.compare(kw,12)
        self.assertGreater(result['work']['old_owned_occurrence_counts_checked'],0)
        for same in (False,True):
            supplied=dict(kw);supplied['banned']=iter(kw['banned'])
            supplied['expected_old_banned']=supplied['banned'] if same else iter(kw['expected_old_banned'])
            other=audit.check(**supplied,capacity=12)
            self.assertEqual(audit.digest(audit.scientific(result)),audit.digest(audit.scientific(other)))
        self.compare(fixture({'10':'\U00010400a\U00010400a','2':'\U00010400a','3':'ab'},{'ab'},seed=['~~']),12)

    def test_observable_corruption_and_missing_shared_identity(self):
        kw=fixture({'10':'abxab','2':'abyab'},{'abxab','abyab'},seed=['~~'])
        result,forward,streams,shared,rows=self.compare(kw,12)
        bad=copy.deepcopy(forward);bad['10'][2][1]+=1
        with self.assertRaises(AssertionError):audit.check(**kw,expected_price_prefix_schedule=bad)
        unpriced={pid:v[0] for pid,v in forward.items()};bad=copy.deepcopy(unpriced);bad['10'][1]+=1
        with self.assertRaises(AssertionError):audit.check(**kw,expected_unpriced_prefix_schedule=bad)
        bad=copy.deepcopy(streams);bad['10'][0]['sha256']='0'*64
        with self.assertRaises(AssertionError):audit.check(**kw,expected_count_streams=bad)
        for value in (shared[0][1]+1,True):
            bad=copy.deepcopy(shared);bad[0][1]=value
            with self.assertRaises(AssertionError):audit.check(**kw,expected_shared_counts=bad)
        bad=copy.deepcopy(result['price_caps']);bad['10'][1]+=1
        with self.assertRaises(AssertionError):audit.check(**kw,expected_price_caps=bad)
        bad=copy.deepcopy(rows);bad[1]['charge']+=1
        with self.assertRaises(AssertionError):audit.check(**kw,capacity=12,expected_price_rows=bad)
        broken=copy.deepcopy(kw);broken['old_pool'].remove('ab')
        broken['old_q']=[0 for pid,text in sorted(broken['texts'].items()) for i in range(len(text)) for j in range(i+1,len(text)+1) if text[i:j] in broken['old_pool']]
        with self.assertRaises(AssertionError):audit.check(**broken)

    def test_key_scalar_shape_rejection_and_optimized_python(self):
        kw=fixture({'10':'abc','2':'bcd'},{'abc','bcd'})
        for value in (-1,True):
            broken=copy.deepcopy(kw);broken['old_q'][0]=value
            with self.assertRaises(AssertionError):audit.check(**broken)
        with self.assertRaises(AssertionError):audit.check(**kw,capacity=True)
        for value in ({1:'one','1':'collision'},{False:'bad'},{'bad':1.5}):
            with self.assertRaises(AssertionError):audit.normalized(value)
        for script in ('import independent;independent.z_counts([97],0)',
                       'import independent;independent.check({},set(),[],[],[],[],1,expected_source_hashes={},expected_old_banned=set())'):
            proc=subprocess.run([sys.executable,'-O','-B','-c',script],cwd=Path(__file__).resolve().parent,capture_output=True,timeout=5)
            self.assertNotEqual(proc.returncode,0);self.assertIn(b'normal assertions required',proc.stderr)

if __name__=='__main__':unittest.main()
