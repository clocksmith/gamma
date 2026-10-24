"""Invented supplied inputs; independent explicit paths, schedules and allocations."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import random
import subprocess
import sys
import unittest
from unittest.mock import patch
import independent as audit
import proof
import test_proof


def prior53():
    spec=importlib.util.spec_from_file_location('owner57_frozen53',Path(__file__).resolve().parents[1]/'potential-tightening-v1/independent.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def fixture(texts,banned=(),seed=(),D=7,rng=None):
    banned=set(banned);rng=rng or random.Random(5701);owners={}
    for (pid,i,j),word in proof.allowed(texts,banned).items():owners.setdefault(word,set()).add(pid)
    alphabet=sorted(set(''.join(texts.values()))|{'~'})
    pool=sorted(set(alphabet)|set(seed)|{w for w,ps in owners.items() if len(ps)>1})
    q=[rng.randrange(40) for pid,t in sorted(texts.items()) for i in range(len(t))
       for j in range(i+1,len(t)+1) if t[i:j] in pool]
    return dict(texts=texts,banned=banned,old_pool=pool,old_q=q,seed=list(seed),alphabet=alphabet,D=D,
        expected_source_hashes={pid:hashlib.sha256(t.encode()).hexdigest() for pid,t in texts.items()},expected_old_banned=banned)


def explicit(kw):
    texts,D=kw['texts'],kw['D'];it=iter(kw['old_q'])
    old={(pid,i,j):next(it) for pid,t in sorted(texts.items()) for i in range(len(t))
         for j in range(i+1,len(t)+1) if t[i:j] in kw['old_pool']}
    potentials={}
    for pid,t in texts.items():
        d=[None]*len(t)+[0]
        for i in range(len(t)-1,-1,-1):
            d[i]=min((9 if j==i+1 else -1)*D+old[pid,i,j]+d[j]
                     for j in range(i+1,len(t)+1) if (pid,i,j) in old)
        potentials[pid]=d
    q={edge:max(0,potentials[edge[0]][edge[1]]-potentials[edge[0]][edge[2]]-
                (9 if edge[2]==edge[1]+1 else -1)*D) for edge in proof.allowed(texts,kw['banned'])}
    return q,potentials


class IndependentTests(unittest.TestCase):
    def compare(self,kw,B=3,exhaustive=False):
        got=audit.check(**kw,capacity=B)
        self.assertEqual(got['base'],prior53().check(**kw,capacity=B))
        q,d=explicit(kw)
        if exhaustive:oracle,_,_=test_proof.ProofTests().check(kw['texts'],kw['banned'],q,B,kw['D'])
        else:oracle=proof.certificate(kw['texts'],kw['banned'],q,B,kw['D'])
        for key in ('owner_caps','owner_prefixes','capped_prefixes','one_owner_prefix','marginal_choices','shared_prefix'):
            self.assertEqual(got[key],oracle[key],key)
        for row,expected in zip(got['rows'],oracle['rows']):
            for key in ('k','charge','one_owner_slots','numerator','integer_lower_bound'):self.assertEqual(row[key],expected[key])
        index=audit.full.Index(kw['texts'],kw['banned']);expected={pid:[] for pid in kw['texts']}
        for gid,g in enumerate(index.groups):
            pid,start=index.positions[g['lo']]
            for length in range(g['first'],g['last']+1):
                word=kw['texts'][pid][start:start+length]
                if word in kw['banned']:continue
                owner=oracle['support'][word]
                if owner is not None:expected[owner].append((oracle['weights'][word],gid,length))
        for pid,values in expected.items():
            values.sort(key=lambda v:(-v[0],v[1],v[2]))
            self.assertEqual(got['owner_entry_counts'][pid],len(values))
            self.assertEqual(got['owner_top_entries'][pid],values[:B])
            schedule=got['owner_suffix_schedule'][pid];text=kw['texts'][pid]
            self.assertEqual(schedule[-1],0)
            for i in range(len(text)):
                options=[schedule[i+1]]+[q[pid,i,j]+schedule[j] for j in range(i+1,len(text)+1)
                         if (pid,i,j) in q and oracle['support'][text[i:j]]==pid]
                self.assertEqual(schedule[i],max(options))
        allowed_one=sum(oracle['support'][word] is not None for word in proof.allowed(kw['texts'],kw['banned']).values())
        self.assertEqual(got['work']['schedule_occurrences_admitted'],allowed_one)
        self.assertEqual(got['work']['schedule_endpoints_inspected'],sum(len(t)*(len(t)+1)//2 for t in kw['texts'].values()))
        self.assertEqual(got['base']['digests']['potentials_sha256'],audit.canonical_digest(d))
        self.assertEqual(got['digests']['rows_sha256'],audit.canonical_digest(got['rows']))
        forward=oracle['owner_schedule_values']
        replayed=audit.check(**kw,capacity=B,expected_prefix_schedule=forward)
        self.assertTrue(replayed['production_forward_schedule_checked'])
        self.assertEqual(replayed['work']['production_forward_positions_checked'],sum(map(len,kw['texts'].values())))
        self.assertEqual(replayed['production_forward_schedule_sha256'],audit.canonical_digest(forward))
        return got

    def test_exhaustive_paths_allocations_random_fixed_q53(self):
        rng=random.Random(5717)
        for _ in range(14):
            texts={str(i):''.join(rng.choice('abc') for _ in range(3)) for i in range(2)}
            self.compare(fixture(texts,set(texts.values()),rng=rng),3,True)
        kw=fixture({'p':'abc'},{'abc'},D=3);kw['old_q']=[0]*len(kw['old_q'])
        got=self.compare(kw,3,True)
        self.assertGreater(got['deltas_vs53'][2]['charge_reduction'],0)

    def test_full_schedule_old_seed_and_capacity_edges(self):
        kw=fixture({'p':'aaaa'},{'aaaa'},seed=['aaa','~~'])
        for B in (0,1,2,8,256):
            got=self.compare(kw,B,B<=2)
            self.assertEqual(got['owner_entry_counts']['p'],3)
            self.assertEqual(len(got['owner_top_entries']['p']),min(B,3))
        self.assertGreater(got['work']['schedule_occurrences_admitted'],3)
        # Fixed q53 case: top1 is aa, whose restricted schedule is 27.
        # An omitted paid character contributes another 4 to the full schedule.
        kw=fixture({'p':'aaaa'},{'aaaa'},seed=['aaa','~~'],D=1)
        kw['old_q']=[4,10,4,10,4,4]  # a,aaa,a,aaa,a,a
        got=self.compare(kw,1,True)
        self.assertEqual(got['owner_top_entries']['p'][0][0],27)
        self.assertEqual(got['owner_caps']['p'],31)
        q,_=explicit(kw);forward=proof.certificate(kw['texts'],kw['banned'],q,1,kw['D'])['owner_schedule_values']
        for change in ('intermediate','bool','missing'):
            bad=copy.deepcopy(forward)
            if change=='intermediate':bad['p'][1]+=1
            elif change=='bool':bad['p'][0]=False
            else:bad.pop('p')
            with self.assertRaises(AssertionError):audit.check(**kw,capacity=1,expected_prefix_schedule=bad)

    def test_banned_shared_prefixes_and_primitive_body_exclusion(self):
        kw=fixture({'10':'abcxabc','2':'abcyabc'},{'abc','abcxabc','abcyabc'},seed=['cx','~~'])
        self.compare(kw,3)
        kw=fixture({'p':'()=>1','q':'x=1'},{'()=>1','x=1','1'})
        with self.assertRaises(AssertionError):audit.check(**kw)

    def test_zero_ties_and_per_owner_storage(self):
        got=self.compare(fixture({'10':'abcd','2':'efgh','3':'ijkl'}),1)
        self.assertEqual(got['work']['owner_top_entries_retained'],3)
        kw=fixture({'b':'xx','a':'yy'},{'xx','yy'});kw['old_q']=[0]*len(kw['old_q'])
        got=self.compare(kw,4,True)
        self.assertEqual(got['marginal_choices'],[('a',1,0),('b',1,0)])
        self.assertTrue(all(row['one_owner_slots']==0 for row in got['rows']))

    def test_original_authority_corruption_and_missing_shared(self):
        kw=fixture({'10':'abca','2':'bcad'},{'abca','bcad'})
        got=audit.check(**kw,capacity=3);base=got['base']['lifted'];D=kw['D']
        cert={'denominator':D,'numerator':base['old_numerator'],'integer_lower_bound':-(-base['old_numerator']//D),
              'relaxed_paths_numerator':sum(base['path_numerators'].values()),'top_capacity_numerator':base['old_charge'],
              'per_program_path_numerators':[base['path_numerators'][p] for p in sorted(base['path_numerators'])]}
        audit.check(**kw,capacity=3,expected_old_certificate=cert,expected_occurrence_sha256=base['occurrence_sha256'])
        for key in cert:
            bad=copy.deepcopy(cert)
            if type(bad[key]) is list:bad[key][0]+=1
            else:bad[key]+=1
            with self.assertRaises(AssertionError):audit.check(**kw,capacity=3,expected_old_certificate=bad)
        for update in ({'old_q':kw['old_q'][:-1]},{'old_q':kw['old_q']+[0]},
                       {'old_q':[True]+kw['old_q'][1:]},{'old_q':[-1]+kw['old_q'][1:]},
                       {'expected_source_hashes':{}},{'expected_occurrence_sha256':'wrong'}):
            with self.assertRaises(AssertionError):audit.check(**(kw|update))
        bad=copy.deepcopy(kw);bad['old_pool'].remove('bc')
        with self.assertRaises(AssertionError):audit.check(**bad)

    def test_index_corruption_and_optimized_guard(self):
        kw=fixture({'a':'abca','b':'bcad'},{'abca','bcad'});constructor=audit.full.Index
        def corrupt(*args,**kwargs):
            index=constructor(*args,**kwargs);index.groups[0]['multiplicity']+=1;return index
        with patch.object(audit.full,'Index',side_effect=corrupt):
            with self.assertRaises(AssertionError):audit.check(**kw)
        code='import independent; independent.check({},set(),[],[],[],[],1,expected_source_hashes={},expected_old_banned=set())'
        proc=subprocess.run([sys.executable,'-O','-B','-c',code],cwd=Path(__file__).resolve().parent,capture_output=True,timeout=5)
        self.assertNotEqual(proc.returncode,0);self.assertIn(b'independent replay requires assertions',proc.stderr)


if __name__=='__main__':unittest.main()
