"""Invented-only item53 independent replay, exhaustive paths and dictionaries."""
import copy
import hashlib
import importlib.util
import itertools
from pathlib import Path
import random
import subprocess
import sys
import unittest
from unittest.mock import patch
import independent as audit
import tighten


def universe(texts, banned):
    result = {}
    for pid, text in texts.items():
        for i in range(len(text)):
            for j in range(i+1, len(text)+1):
                if text[i:j] not in banned:
                    result.setdefault(text[i:j], []).append((pid, i, j))
    return result


def fixture(texts, banned=(), seed=(), rng=None, pool=None, D=11):
    rng = rng or random.Random(53017); banned = set(banned)
    entries = universe(texts, banned); alphabet = sorted(set(''.join(texts.values()))|{'z'})
    if pool is None:
        pool = sorted(set(alphabet)|set(seed)|{w for w, occ in entries.items()
                      if len(w)>1 and len({p for p, _, _ in occ})>1})
    q = [rng.randrange(90) for pid, text in sorted(texts.items()) for i in range(len(text))
         for j in range(i+1, len(text)+1) if text[i:j] in pool]
    return dict(texts=texts, banned=banned, old_pool=pool, old_q=q, seed=list(seed), alphabet=alphabet, D=D,
                expected_source_hashes={p:hashlib.sha256(t.encode()).hexdigest() for p,t in texts.items()},
                expected_old_banned=banned)


def explicit(kw):
    texts, D = kw['texts'], kw['D']; entries = universe(texts,kw['banned'])
    q = iter(kw['old_q'])
    old = {(p,i,j):next(q) for p,t in sorted(texts.items()) for i in range(len(t))
           for j in range(i+1,len(t)+1) if t[i:j] in kw['old_pool']}
    potentials = {}; weights = {name:dict.fromkeys(entries,0) for name in ('lifted','tightened')}
    oldweights = dict.fromkeys(kw['old_pool'],0); tightweights = dict(oldweights); reduction = []
    for p,t in texts.items():
        d = [None]*len(t)+[0]
        for i in range(len(t)-1,-1,-1):
            d[i] = min((9 if j==i+1 else -1)*D+old[p,i,j]+d[j]
                       for j in range(i+1,len(t)+1) if (p,i,j) in old)
        potentials[p] = d
        for name in weights:
            full = [None]*len(t)+[0]
            for i in range(len(t)-1,-1,-1):
                choices = []
                for j in range(i+1,len(t)+1):
                    word=t[i:j]
                    if word not in entries:continue
                    base=(9 if j==i+1 else -1)*D
                    minimum=max(0,d[i]-d[j]-base)
                    penalty=old.get((p,i,j),minimum) if name=='lifted' else minimum
                    weights[name][word]+=penalty;choices.append(base+penalty+full[j])
                    if name=='tightened' and (p,i,j) in old:
                        assert minimum<=old[p,i,j]
                        oldweights[word]+=old[p,i,j];tightweights[word]+=minimum
                        reduction.append(old[p,i,j]-minimum)
                full[i]=min(choices)
            assert full==d
    return entries, weights, potentials, oldweights, tightweights, reduction


class IndependentTests(unittest.TestCase):
    def compare(self, kw, capacity=3):
        result=audit.check(**kw,capacity=capacity)
        production=tighten.Tighten(kw['texts'],kw['banned'],kw['old_pool'],kw['old_q'],kw['seed'],kw['alphabet'],kw['D'],
          old_source_hashes=kw['expected_source_hashes'],old_banned=kw['expected_old_banned']).certificate(capacity)
        for key in ('lifted','tightened','new_only_class_counts','new_only_top_entries','digests','reductions','deltas'):
            self.assertEqual(result[key],production[key],key)
        entries,weights,d,oldweights,tightweights,reductions=explicit(kw)
        self.assertEqual(result['digests']['potentials_sha256'],audit.canonical_digest(d))
        self.assertEqual(result['digests']['old_weights_sha256'],audit.canonical_digest(list(oldweights.values())))
        self.assertEqual(result['digests']['tightened_old_weights_sha256'],audit.canonical_digest(list(tightweights.values())))
        self.assertEqual(result['reductions']['old_occurrences_reduced'],sum(v>0 for v in reductions))
        self.assertEqual(result['reductions']['old_multiplier_reduction'],sum(reductions))
        self.assertEqual(result['reductions']['old_entries_reduced'],sum(oldweights[w]>tightweights[w] for w in oldweights))
        index=audit.full.Index(kw['texts'],kw['banned'])
        owners={w:len({p for p,_,_ in occ}) for w,occ in entries.items()}
        for name in weights:
            self.assertEqual(result[name]['path_numerators'],{p:ds[0] for p,ds in d.items()})
            for support in (1,2):
                rows=[]
                for gid,g in enumerate(index.groups):
                    p,i=index.positions[g['lo']]
                    for length in range(g['first'],g['last']+1):
                        word=kw['texts'][p][i:i+length]
                        if word in entries and min(owners[word],2)==support:rows.append((weights[name][word],gid,length))
                rows.sort(key=lambda x:(-x[0],x[1],x[2]))
                self.assertEqual(result[name]['top_entries'][support],rows[:capacity])
        self.assertEqual(result['work']['streamed_allowed_depths'],len(entries))
        self.assertEqual(result['work']['old_bellman_edges_checked'],len(kw['old_q']))
        return result,entries,weights,owners

    def test_random_fresh_paths_all_weights_top_ties_and_reductions(self):
        rng=random.Random(5317)
        for _ in range(60):
            texts={str(p):''.join(rng.choice('abc') for _ in range(rng.randrange(2,7))) for p in range(3)}
            banned=set(texts.values());entries=universe(texts,banned)
            seed=[w for w,o in sorted(entries.items()) if len(w)>1 and len({p for p,_,_ in o})==1][:2]+['zz']
            self.compare(fixture(texts,banned,seed,rng),rng.randrange(6))

    def test_exhaustive_subset_allocations_and_weak_duality(self):
        kw=fixture({'a':'abac','b':'baca'},{'abac','baca'},['zz'])
        got,entries,weights,owners=self.compare(kw,3)
        maxima={name:[0]*4 for name in weights}
        for size in range(4):
            for selected in itertools.combinations(entries,size):
                one=sum(owners[w]==1 for w in selected)
                for name in weights:
                    charge=sum(weights[name][w] for w in selected)
                    for k in range(one,4):maxima[name][k]=max(maxima[name][k],charge)
                total=0
                for text in kw['texts'].values():
                    path=[0]+[None]*len(text)
                    for end in range(1,len(text)+1):
                        choices=[path[end-len(w)]+(9 if len(w)==1 else -1) for w in selected
                                 if len(w)<=end and text[end-len(w):end]==w and path[end-len(w)] is not None]
                        path[end]=min(choices) if choices else None
                    if path[-1] is None:break
                    total+=path[-1]
                else:
                    for name in weights:
                        for k in range(one,4):self.assertGreaterEqual(total*kw['D'],got[name]['rows'][k]['numerator'])
        for name in weights:self.assertEqual(maxima[name],[r['charge'] for r in got[name]['rows']])

    def test_new_entry_after_old_falls_strict_zero_and_rounded_gain(self):
        for aq,reduction,gain in ((500,204,True),(297,1,False),(50,0,False)):
            kw=fixture({'0':'abcd'},{'abcd'},['ab'],D=7)
            # Authoritative start/end order: a,ab,b,c,d.
            kw['old_q']=[aq,0,100,0,0]
            got,_,_,_=self.compare(kw,1)
            self.assertGreater(got['reductions']['old_occurrences_reduced'],0)
            self.assertEqual(got['deltas'][1]['charge_reduction'],reduction)
            self.assertEqual(got['deltas'][1]['integer_bound_gain']>0,gain)
            if reduction:self.assertNotEqual(got['lifted']['top_entries'][1][0][1:],got['tightened']['top_entries'][1][0][1:])

    def test_all257_paid_characters_absent_entries_repeated_and_unique(self):
        kw=fixture({'a':'aaaaabaaaa','b':'bcabc','c':'bcabc'},{'aaaa','aaaaabaaaa','bcabc'},['aaaab','zz'])
        got,entries,_,owners=self.compare(kw,256)
        self.assertEqual(len(got['tightened']['rows']),257)
        self.assertGreater(got['work']['new_occurrence_contributions'],got['work']['new_entries_streamed'])
        self.assertEqual(owners['aaa'],1);self.assertEqual(owners['bc'],2);self.assertNotIn('z',entries)
        kw=fixture({'a':'abcdefghijklmnop','b':'ap'},{'abcdefghijklmnop','bcde','efg'},['cdef','zz'])
        kw['old_q']=[0]*len(kw['old_q']);got,_,_,_=self.compare(kw,256)
        self.assertEqual(got['work']['new_occurrence_contributions'],got['work']['new_entries_streamed'])
        self.assertEqual(got['new_only_class_counts'][2],0)
        kw=fixture({'a':'ab','b':'ac'},{'ab','ac'},['zz']);got,_,_,_=self.compare(kw,256)
        self.assertEqual(got['tightened']['class_counts'],{1:2,2:1})
        self.assertEqual(got['reductions']['absent_old_entries'],2)
        # Primitive-body exclusion may collide with an old paid singleton.
        kw=fixture({'a':'()=>1','b':'x=1'},{'()=>1','x=1','1'})
        with self.assertRaises(AssertionError):audit.check(**kw)

    def test_frozen50_baseline_identity_and_old_certificate_corruption(self):
        kw=fixture({'10':'abca','2':'bcad'},{'abca','bcad'})
        spec=importlib.util.spec_from_file_location('test53_frozen50',Path(__file__).resolve().parents[1]/'potential-lift-certificate-v1/independent.py')
        old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
        got=audit.check(**kw);prior=old.check(**kw)
        for k,v in got['lifted'].items():self.assertEqual(v,prior[k],k)
        p=got['lifted'];cert={'denominator':kw['D'],'numerator':p['old_numerator'],
          'integer_lower_bound':-(-p['old_numerator']//kw['D']),'relaxed_paths_numerator':sum(p['path_numerators'].values()),
          'top_capacity_numerator':p['old_charge'],'per_program_path_numerators':[p['path_numerators'][pid] for pid in sorted(p['path_numerators'])]}
        audit.check(**kw,expected_old_certificate=cert,expected_occurrence_sha256=p['occurrence_sha256'])
        for key in cert:
            damaged=copy.deepcopy(cert)
            if type(damaged[key]) is list:damaged[key][0]+=1
            else:damaged[key]+=1
            with self.assertRaises(AssertionError):audit.check(**kw,expected_old_certificate=damaged)
        for update in ({'expected_source_hashes':{}},{'expected_old_banned':{'wrong'}},{'old_q':kw['old_q'][:-1]},
                       {'old_q':kw['old_q']+[0]},{'old_q':[True]+kw['old_q'][1:]},{'old_q':[-1]+kw['old_q'][1:]},
                       {'old_q':[.5]+kw['old_q'][1:]},{'expected_occurrence_sha256':'wrong'}):
            with self.assertRaises(AssertionError):audit.check(**(kw|update))

    def test_pool_and_shared_completeness_fail_closed(self):
        texts={'a':'abc','b':'abd'};kw=fixture(texts)
        for pool in ([w for w in kw['old_pool'] if w!='ab'],sorted(kw['old_pool']+['bc'])):
            with self.assertRaises(AssertionError):audit.check(**fixture(texts,pool=pool))
        kw=fixture({'a':'abca','b':'bcad'},{'abca','bcad'});constructor=audit.full.Index
        for corruption in ('group','lcp','ban','multiplicity'):
            def changed(*a,**k):
                value=constructor(*a,**k)
                if corruption=='group':value.groups.pop()
                elif corruption=='lcp':value.lcp[-1]+=1
                elif corruption=='ban':next(g for g in value.groups if g['excluded_lengths'])['excluded_lengths'].clear()
                else:value.groups[0]['multiplicity']+=1
                return value
            with patch.object(audit.full,'Index',side_effect=changed):
                with self.assertRaises(AssertionError):audit.check(**kw)

    def test_optimized_python_rejected_before_inputs(self):
        code='import independent; independent.check({},set(),[],[],[],[],1,expected_source_hashes={},expected_old_banned=set())'
        result=subprocess.run([sys.executable,'-O','-B','-c',code],cwd=Path(__file__).resolve().parent,capture_output=True,timeout=10)
        self.assertNotEqual(result.returncode,0);self.assertIn(b'independent replay requires assertions',result.stderr)


if __name__=='__main__':unittest.main()
