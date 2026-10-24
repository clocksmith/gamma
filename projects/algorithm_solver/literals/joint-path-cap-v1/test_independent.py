"""Invented complete oracles and deliberate authority/recurrence corruption."""
import copy
import importlib.util
import itertools
from pathlib import Path
import random
import subprocess
import sys
import unittest
from unittest.mock import patch

import independent as audit
import proof
import test_proof

HERE = Path(__file__).resolve().parent


def load(name,path,overrides=None):
    overrides = overrides or {}; saved = {key:sys.modules.get(key) for key in overrides}
    try:
        sys.modules.update(overrides)
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module
    finally:
        for key,value in saved.items():
            if value is None:sys.modules.pop(key,None)
            else:sys.modules[key]=value


# Reuse only invented fixture generation from57, loaded with isolated imports.
proof57=load('joint60_fixture_proof57',HERE.parent/'owner-path-cap-v1/proof.py')
tests57=load('joint60_fixture_tests57',HERE.parent/'owner-path-cap-v1/test_proof.py',{'proof':proof57})
fixture57=load('joint60_fixtures57',HERE.parent/'owner-path-cap-v1/test_independent.py',
               {'proof':proof57,'test_proof':tests57,'independent':audit.parent})
fixture=fixture57.fixture
explicit=fixture57.explicit


class IndependentTests(unittest.TestCase):
    def compare(self,kw,B=3,exhaustive=False):
        got=audit.check(**kw,capacity=B)
        q,d=explicit(kw)
        if exhaustive:oracle,_,_=test_proof.ProofTests().check(kw['texts'],kw['banned'],q,B,kw['D'])
        else:oracle=proof.certificate(kw['texts'],kw['banned'],q,B,kw['D'])
        for key in ('local_shared_prefixes','all_caps'):
            self.assertEqual(got[key],oracle[key])
        self.assertEqual(got['base57']['shared_prefix'],oracle['shared_prefix'])
        self.assertEqual(got['base57']['owner_prefixes'],oracle['owner_prefixes'])
        self.assertEqual(audit.digest(d),got['base57']['base']['digests']['potentials_sha256'])
        for row,expected in zip(got['rows'],oracle['rows']):
            for key in ('k','charge','one_owner_slots','numerator','integer_lower_bound'):
                self.assertEqual(row[key],expected[key])
            self.assertEqual(row['shared_slots'],min(B-row['one_owner_slots'],len(oracle['shared_prefix'])-1))
        for split,expected in zip(got['split_rows'],oracle['alternatives']):
            for key in ('one_owner_slots','shared_slots','joint_charge','prior57_charge','charge','allocation_choices'):
                self.assertEqual(split[key],expected[key],key)
            self.assertEqual(split['baseline'],sum(v[0] for v in expected['owner_functions'].values()))
            # Independent exhaustive exactly-j numerical allocation.
            owners=sorted(expected['owner_functions']);fs=expected['owner_functions'];j=split['one_owner_slots']
            self.assertEqual(split['joint_charge'],max(sum(fs[p][n] for p,n in zip(owners,counts))
                for counts in itertools.product(*(range(len(fs[p])) for p in owners)) if sum(counts)==j))
        index=audit.parent.full.Index(kw['texts'],kw['banned']);shared=[]
        for gid,g in enumerate(index.groups):
            pid,start=index.positions[g['lo']]
            for length in range(g['first'],g['last']+1):
                word=kw['texts'][pid][start:start+length]
                if word in kw['banned'] or oracle['support'][word] is not None:continue
                shared.append((gid,length,word))
        for pid,text in kw['texts'].items():
            local=oracle['local_weights'][pid]
            expected=sorted(((local.get(w,0),gid,length) for gid,length,w in shared),key=lambda v:(-v[0],v[1],v[2]))[:B]
            self.assertEqual(got['local_shared_top_entries'][pid],expected)
            self.assertEqual(got['local_shared_counts'][pid],{'available':len(shared),'occurring':sum(w in text for _,_,w in shared),'positive':sum(local.get(w,0)>0 for _,_,w in shared)})
            schedule=got['all_suffix_schedule'][pid]
            self.assertEqual(schedule[-1],0)
            for i in range(len(text)):
                self.assertEqual(schedule[i],max([schedule[i+1]]+[q[pid,i,j]+schedule[j] for j in range(i+1,len(text)+1) if (pid,i,j) in q]))
        forward=oracle['all_schedule_values'];one=oracle['one_owner_schedule_values']
        checked=audit.check(**kw,capacity=B,expected_prefix_schedule=forward,expected_base57_prefix_schedule=one)
        for key in audit.COMMON:self.assertEqual(checked[key],got[key])
        self.assertTrue(checked['production_forward_schedule_checked'])
        self.assertTrue(checked['base57']['production_forward_schedule_checked'])
        self.assertEqual(checked['production_forward_schedule_sha256'],audit.digest(forward))
        self.assertEqual(checked['work']['production_forward_positions_checked'],sum(map(len,kw['texts'].values())))
        endpoints=sum(len(t)*(len(t)+1)//2 for t in kw['texts'].values())
        self.assertEqual(checked['work']['production_forward_endpoints_inspected'],endpoints)
        self.assertEqual(checked['work']['schedule_endpoints_inspected'],endpoints)
        self.assertEqual(checked['work']['schedule_occurrences_admitted'],len(q))
        return got,oracle

    def test_strict_fixed_q53_overlap_and_small_exhaustive(self):
        texts={'p':'abc','q':'abd'}
        for D in (1,3):
            kw=fixture(texts,set(texts.values()),D=D)
            kw['old_q']=[0 if j-i==1 else D*(9*(j-i)+1) for pid,t in sorted(texts.items())
                         for i in range(len(t)) for j in range(i+1,len(t)+1) if t[i:j] in kw['old_pool']]
            got,_=self.compare(kw,3,True)
            self.assertEqual(got['base57']['rows'][2]['charge'],76*D)
            self.assertEqual(got['rows'][2]['charge'],38*D)
            self.assertEqual(got['rows'][2]['integer_lower_bound'],16)
        rng=random.Random(6061)
        for _ in range(12):
            texts={str(i):''.join(rng.choice('abc') for _ in range(3)) for i in range(2)}
            self.compare(fixture(texts,set(texts.values()),rng=rng),3,True)

    def test_shared_global_coupling_and_local_outside_global_top(self):
        kw=fixture({'p':'ab','q':'ab'},{'ab'},D=1);kw['old_q']=[10,0,0,10]
        got,_=self.compare(kw,1,True)
        self.assertEqual(got['split_rows'][0]['joint_charge'],20)
        self.assertEqual(got['split_rows'][0]['prior57_charge'],10)
        self.assertEqual(got['rows'][0]['charge'],10)
        texts={'p':'ab','q':'ac','r':'bc'}
        kw=fixture(texts,set(texts.values()),D=1);kw['old_q']=[10,0,0,10,0,10]
        got,_=self.compare(kw,1,True)
        local=got['local_shared_top_entries']['p'][0][1:]
        global_top=got['base57']['base']['tightened']['top_entries'][2][0][1:]
        self.assertNotEqual(local,global_top)
        self.assertEqual(got['local_shared_counts']['p'],{'available':3,'occurring':2,'positive':1})
        zeros,_=self.compare(kw,4)
        self.assertEqual(len(zeros['local_shared_top_entries']['p']),3)
        self.assertEqual([v[0] for v in zeros['local_shared_top_entries']['p']],[10,0,0])

    def test_full_arc_schedule_requires_low_ranked_arc(self):
        kw=fixture({'p':'aaaa'},{'aaaa'},seed=['aaa','~~'],D=1)
        kw['old_q']=[4,10,4,10,4,4]
        got,_=self.compare(kw,1,True)
        self.assertEqual(got['base57']['owner_top_entries']['p'][0][0],27)
        self.assertEqual(got['all_caps']['p'],31)
        self.assertEqual(got['work']['schedule_occurrences_admitted'],9)

    def test_bans_repeats_zero_finite_capacity_and_unicode(self):
        kw=fixture({'10':'abcxabc','2':'abcyabc'},{'abc','abcxabc','abcyabc'},seed=['cx','~~'])
        self.compare(kw,3)
        kw=fixture({'a':'xx','b':'yy'},{'xx','yy'});kw['old_q']=[0]*len(kw['old_q'])
        for B in (0,1,2,8):self.compare(kw,B,True)
        self.compare(fixture({'a':'éλx','b':'éλy'},{'éλx','éλy'}),3,True)

    def test_forward_every_recurrence_and_strict_shape(self):
        kw=fixture({'p':'aaaa'},{'aaaa'},seed=['aaa'],D=1);kw['old_q']=[4,10,4,10,4,4]
        _,oracle=self.compare(kw,1)
        for key in ('expected_prefix_schedule','expected_base57_prefix_schedule'):
            good=oracle['all_schedule_values' if key=='expected_prefix_schedule' else 'one_owner_schedule_values']
            for how in ('intermediate','bool','missing','short','negative'):
                bad=copy.deepcopy(good)
                if how=='intermediate':bad['p'][1]+=1 # final cap unchanged
                elif how=='bool':bad['p'][0]=False
                elif how=='missing':bad.pop('p')
                elif how=='short':bad['p'].pop()
                else:bad['p'][0]=-1
                with self.subTest(key=key,corruption=how):
                    with self.assertRaises(AssertionError):audit.check(**kw,capacity=1,**{key:bad})

    def test_old_authority_missing_shared_order_and_q_corruption(self):
        kw=fixture({'a':'abca','b':'bcad'},{'abca','bcad'})
        got,_=self.compare(kw,3);base=got['base57']['base']['tightened']
        cert={'denominator':kw['D'],'numerator':base['old_numerator'],'integer_lower_bound':-(-base['old_numerator']//kw['D']),
            'relaxed_paths_numerator':sum(base['path_numerators'].values()),'top_capacity_numerator':base['old_charge'],
            'per_program_path_numerators':[base['path_numerators'][p] for p in sorted(base['path_numerators'])]}
        audit.check(**kw,capacity=3,expected_old_certificate=cert,expected_occurrence_sha256=base['occurrence_sha256'])
        for update in ({'old_q':[True]+kw['old_q'][1:]},{'old_q':[-1]+kw['old_q'][1:]},
                       {'old_q':kw['old_q'][:-1]},{'old_q':kw['old_q']+[0]},
                       {'expected_occurrence_sha256':'wrong'},{'expected_source_hashes':{}},
                       {'old_pool':list(reversed(kw['old_pool']))}):
            with self.assertRaises(AssertionError):audit.check(**(kw|update),capacity=3)
        bad=copy.deepcopy(kw);bad['old_pool'].remove('bc')
        # Rebuild correctly sized multipliers, so full-shared completeness itself fails.
        old=iter(kw['old_q']);bad['old_q']=[]
        for pid,text in sorted(kw['texts'].items()):
            for i in range(len(text)):
                for j in range(i+1,len(text)+1):
                    if text[i:j] in kw['old_pool']:
                        v=next(old)
                        if text[i:j] in bad['old_pool']:bad['old_q'].append(v)
        with self.assertRaisesRegex(AssertionError,'missing old shared'):audit.check(**bad,capacity=3)
        bad=copy.deepcopy(kw);bad['old_q']=[q+100 for q in kw['old_q']]
        with self.assertRaises(AssertionError):audit.check(**bad,capacity=3,expected_old_certificate=cert)
        # Old q contains slack. Full local sums must use q53, not those old values.
        self.assertNotEqual(got['base57']['base']['digests']['old_weights_sha256'],got['base57']['base']['digests']['tightened_old_weights_sha256'])

    def test_fresh_reconstruction_rejects_corrupted_base_terms(self):
        kw=fixture({'a':'abca','b':'bcad'},{'abca','bcad'})
        baseline=audit.parent.check(**kw,capacity=3)
        for how in ('d','support','weights','top'):
            bad=copy.deepcopy(baseline)
            if how=='d':bad['base']['digests']['potentials_sha256']='wrong'
            elif how=='support':bad['base']['tightened']['class_counts'][2]+=1
            elif how=='weights':bad['base']['digests']['tightened_old_weights_sha256']='wrong'
            else:bad['base']['tightened']['top_entries'][2][0]=(100000,0,1)
            with patch.object(audit.parent,'check',return_value=bad):
                with self.assertRaises(AssertionError):audit.check(**kw,capacity=3)

    def test_optimized_python_rejected(self):
        code='import independent; independent.check({},set(),[],[],[],[],1,expected_source_hashes={},expected_old_banned=set())'
        proc=subprocess.run([sys.executable,'-O','-B','-c',code],cwd=HERE,capture_output=True,text=True,timeout=5)
        self.assertNotEqual(proc.returncode,0);self.assertIn('independent replay requires assertions',proc.stderr)


if __name__=='__main__':unittest.main()
