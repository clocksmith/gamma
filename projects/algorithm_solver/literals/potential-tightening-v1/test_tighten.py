"""Invented exhaustive supplied strings only; no corpus/complexity measurement."""
import importlib.util
import itertools
from pathlib import Path
import random
import subprocess
import sys
import unittest

import tighten as t


def load50():
    spec=importlib.util.spec_from_file_location('tighten_test_frozen50',
        Path(__file__).resolve().parents[1]/'potential-lift-certificate-v1/prototype.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def owners(texts,banned):
    result={}
    for pid,text in texts.items():
        for i in range(len(text)):
            for j in range(i+1,len(text)+1):
                if text[i:j] not in banned:result.setdefault(text[i:j],set()).add(pid)
    return result


def fixture(texts,banned=(),seed=(),rng=None,D=7,values=None):
    rng=rng or random.Random(53);banned=set(banned);support=owners(texts,banned)
    alphabet=sorted(set(''.join(texts.values()))|{'z'})
    pool=sorted({w for w,pids in support.items() if len(w)>1 and len(pids)>1}|set(alphabet)|set(seed))
    byedge={};q=[]
    for pid,text in sorted(texts.items()):
        for i in range(len(text)):
            for j in range(i+1,len(text)+1):
                if text[i:j] in pool:
                    value=rng.randrange(70) if values is None else values[pid,i,j]
                    q.append(value);byedge[pid,i,j]=value
    return dict(texts=texts,banned=banned,old_pool=pool,old_q=q,seed=list(seed),alphabet=alphabet,
                denominator=D,old_source_hashes=t.source_hashes(texts),old_banned=banned),byedge


def word(model,gid,length):
    g=model.index.groups[gid];pid,start=model.positions[g['lo']]
    return model.texts[pid][start:start+length]


def explicit(model,banned,old):
    support=owners(model.texts,banned);weights={name:dict.fromkeys(support,0) for name in ('lifted','tightened')}
    paths={name:{} for name in weights}
    for name in weights:
        for pid,text in model.texts.items():
            d=[None]*len(text)+[0]
            for i in range(len(text)-1,-1,-1):
                choices=[]
                for j in range(i+1,len(text)+1):
                    w=text[i:j]
                    if w not in support:continue
                    base=9 if j-i==1 else -1
                    minimum=max(0,model.d[pid][i]-model.d[pid][j]-base*model.D)
                    q=old.get((pid,i,j),minimum) if name=='lifted' else minimum
                    assert q==model.penalty(pid,i,j,tighten_old=name=='tightened')
                    assert base*model.D+q+model.d[pid][j]>=model.d[pid][i]
                    weights[name][w]+=q;choices.append(base*model.D+q+d[j])
                d[i]=min(choices)
            paths[name][pid]=d
    return support,weights,paths


class TightenTests(unittest.TestCase):
    def check(self,kw,old,capacity):
        model=t.Tighten(**kw);got=model.certificate(capacity)
        support,weights,paths=explicit(model,kw['banned'],old)
        for name in ('lifted','tightened'):
            self.assertEqual(paths[name],model.d)
            proof=got[name]
            self.assertEqual(proof['class_counts'],{s:sum((1 if len(v)==1 else 2)==s for v in support.values()) for s in (1,2)})
            for s in (1,2):
                entries=[]
                for gid,g in enumerate(model.index.groups):
                    for length in range(g['first'],g['last']+1):
                        if length in g['excluded_lengths']:continue
                        w=word(model,gid,length)
                        if (1 if len(support[w])==1 else 2)==s:entries.append((weights[name][w],gid,length))
                entries.sort(key=lambda row:(-row[0],row[1],row[2]))
                self.assertEqual(proof['top_entries'][s],entries[:capacity])
                new=[row for row in entries if word(model,row[1],row[2]) not in kw['old_pool']]
                self.assertEqual(got['new_only_top_entries'][s],new[:capacity])
            for row in proof['rows']:
                b=row['integer_lower_bound'];n=row['numerator']
                self.assertLess((b-1)*model.D,n);self.assertGreaterEqual(b*model.D,n)
            self.assertEqual(got['digests'][name+'_proof_sha256'],t.digest(proof))
        reductions=[old[pid,i,j]-model.penalty(pid,i,j) for pid,i,j in old]
        self.assertEqual(got['reductions']['old_occurrences_reduced'],sum(v>0 for v in reductions))
        self.assertEqual(got['reductions']['old_multiplier_reduction'],sum(reductions))
        # Compare complete scientific50 proof and digest, not just a scalar bound.
        reference=load50().Lift(**kw).certificate(capacity)
        self.assertEqual(got['lifted'],{k:reference[k] for k in got['lifted']})
        return model,got,support,weights

    def test_random_explicit_every_suffix_weight_class_and_top(self):
        rng=random.Random(5301);strict=0
        for _ in range(70):
            texts={str(i):''.join(rng.choice('abc') for _ in range(rng.randrange(2,7))) for i in range(3)}
            banned={text for text in texts.values() if len(text)>1}
            support=owners(texts,banned)
            seed=sorted(w for w,pids in support.items() if len(pids)==1 and len(w)>1)[:2]+['zz']
            kw,old=fixture(texts,banned,seed,rng)
            _,got,_,_=self.check(kw,old,rng.randrange(0,6));strict+=got['reductions']['strict_charge_budgets']
        self.assertGreater(strict,0)

    def test_exhaustive_dictionaries_weak_duality_and_allocations(self):
        rng=random.Random(5302)
        for _ in range(12):
            texts={str(i):''.join(rng.choice('ab') for _ in range(4)) for i in range(2)}
            kw,old=fixture(texts,set(texts.values()),rng=rng)
            model,got,support,weights=self.check(kw,old,3)
            maxima={name:[0]*4 for name in weights}
            for size in range(4):
                for selected in itertools.combinations(support,size):
                    one=sum(len(support[w])==1 for w in selected)
                    for name in weights:
                        value=sum(weights[name][w] for w in selected)
                        for k in range(one,4):maxima[name][k]=max(maxima[name][k],value)
                    total=0
                    for text in texts.values():
                        d=[None]*len(text)+[0]
                        for i in range(len(text)-1,-1,-1):
                            choices=[(9 if len(w)==1 else -1)+d[i+len(w)] for w in selected
                                     if text.startswith(w,i) and d[i+len(w)] is not None]
                            d[i]=min(choices) if choices else None
                        if d[0] is None:break
                        total+=d[0]
                    else:
                        for k in range(one,4):self.assertGreaterEqual(total,got['tightened']['rows'][k]['integer_lower_bound'])
            for name in maxima:self.assertEqual(maxima[name],[row['charge'] for row in got[name]['rows']])

    def test_new_only_entry_replaces_dropped_old_top_no_gain_and_ceiling(self):
        # Old a is slack; bcd is new. Their weights cross after tightening.
        for aq,expected_reduction,expect_ceil in ((500,204,True),(297,1,False),(50,0,False)):
            values={('0',0,1):aq,('0',0,2):0,('0',1,2):100,('0',2,3):0,('0',3,4):0}
            kw,old=fixture({'0':'abcd'},{'abcd'},['ab'],D=7,values=values)
            model,got,_,_=self.check(kw,old,1)
            self.assertGreater(got['reductions']['old_occurrences_reduced'],0)
            self.assertEqual(got['deltas'][1]['charge_reduction'],expected_reduction)
            self.assertEqual(got['deltas'][1]['integer_bound_gain']>0,expect_ceil)
            if expected_reduction:
                a=got['lifted']['top_entries'][1][0];b=got['tightened']['top_entries'][1][0]
                self.assertEqual(word(model,a[1],a[2]),'a');self.assertEqual(word(model,b[1],b[2]),'bcd')
                self.assertNotIn(b,got['lifted']['top_entries'][1])

    def test_paid_one_owner_chars_absent_entries_all257_and_global_bans(self):
        kw,old=fixture({'0':'ab','1':'ac'},{'ab','ac'},['zz'])
        model,got,support,_=self.check(kw,old,256)
        self.assertEqual(support['b'],{'0'});self.assertNotIn('z',support)
        self.assertEqual(got['tightened']['class_counts'],{1:2,2:1})
        self.assertEqual(len(got['tightened']['rows']),257)
        self.assertEqual(got['reductions']['absent_old_entries'],2)
        for proof in (got['lifted'],got['tightened']):self.assertEqual(proof['rows'][0]['one_owner_slots'],0)
        # Supplied global body strings exclude every occurrence, not just the
        # source which originally supplied the body. Parser binding is outside
        # this supplied-input kernel and remains a later execution check.
        kw,old=fixture({'0':'abcab','1':'cabca'},{'abcab','cabca','abc'},['bca','zz'])
        _,got,support,_=self.check(kw,old,4);self.assertNotIn('abc',support)
        # A supplied primitive arrow body can be a single character. The old
        # alphabet edge would then be banned: refuse, never drop that ban.
        kw,_=fixture({'0':'()=>1','1':'x=1'},{'()=>1','x=1','1'})
        with self.assertRaises(AssertionError):t.Tighten(**kw)

    def test_repeated_overlaps_unique_split_bans_and_deterministic_zero_ties(self):
        kw,old=fixture({'0':'aaaaabaaaa','1':'bcabc'},{'aaaa','aaaaabaaaa','bcabc'},['aaaab','zz'])
        _,got,_,_=self.check(kw,old,5)
        self.assertGreater(got['work']['repeated_new_occurrence_contributions'],0)
        kw,old=fixture({'0':'abcdefghijk','1':'ak'},{'abcdefghijk','bcde','efg'},['cdef','zz'])
        _,got,_,_=self.check(kw,old,4)
        self.assertGreater(got['work']['unique_range_queries'],0)
        self.assertLessEqual(got['work']['unique_entries_extracted'],4)
        kw,old=fixture({'0':'abcdef'},{'abcdef'},['abcde'])
        kw['old_q']=[0]*len(kw['old_q']);old=dict.fromkeys(old,0)
        model,got,_,weights=self.check(kw,old,256)
        self.assertEqual([weights['tightened'][w] for w in ('ab','abc','abcd')],[0,0,0])
        # Full oracle equality above checks earliest-length tie selection even
        # though the minimum endpoint potential is at the other end of a range.
        heap=t.Top(2)
        for row in ((0,2,3),(0,1,4),(0,1,2),(0,3,1)):heap.add(*row)
        self.assertEqual(heap.entries(),[(0,1,2),(0,1,4)])
        entries={1:[(0,1,2)],2:[(0,2,1)]}
        rows=t.allocations(entries,{1:1,2:1},1,-1,7)
        self.assertEqual(rows[1]['one_owner_slots'],0);self.assertEqual(rows[1]['integer_lower_bound'],0)

    def test_input_identity_order_q_parent_replay_and_pool_scope_failures(self):
        kw,old=fixture({'10':'abca','2':'bcad'},{'abca','bcad'})
        model=t.Tighten(**kw);proof=model.certificate(3)['lifted']
        certificate={'denominator':7,'relaxed_paths_numerator':sum(proof['path_numerators'].values()),
          'top_capacity_numerator':proof['old_charge'],'numerator':proof['old_numerator'],
          'integer_lower_bound':-(-proof['old_numerator']//7),
          'per_program_path_numerators':[proof['path_numerators'][p] for p in sorted(model.texts)]}
        t.Tighten(**kw,expected_old_certificate=certificate,expected_occurrence_sha256=model.occurrence_sha256).certificate(3)
        for update in ({'old_source_hashes':{}},{'old_banned':{'wrong'}},{'old_q':kw['old_q'][:-1]},
                       {'old_q':kw['old_q']+[0]},{'old_q':[True]+kw['old_q'][1:]},
                       {'old_q':[-1]+kw['old_q'][1:]},{'old_q':[.5]+kw['old_q'][1:]},
                       {'expected_occurrence_sha256':'wrong'},
                       {'expected_old_certificate':{**certificate,'top_capacity_numerator':True}}):
            with self.assertRaises(AssertionError):t.Tighten(**(kw|update)).certificate(3)
        for pool in ([w for w in kw['old_pool'] if w!='bc'],sorted(kw['old_pool']+['bcaX'])):
            q=[0 for pid,text in sorted(kw['texts'].items()) for i in range(len(text))
               for j in range(i+1,len(text)+1) if text[i:j] in pool]
            with self.assertRaises(AssertionError):t.Tighten(**(kw|{'old_pool':pool,'old_q':q}))

    def test_optimized_python_is_rejected(self):
        code='import tighten\ntry: tighten.Tighten({},set(),[],[],[],[],1,old_source_hashes={},old_banned=set())\nexcept RuntimeError: pass\nelse: raise RuntimeError("checks disabled")'
        result=subprocess.run([sys.executable,'-O','-B','-c',code],cwd=Path(__file__).resolve().parent,capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
