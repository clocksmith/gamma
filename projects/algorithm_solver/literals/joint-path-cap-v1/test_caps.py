"""Invented supplied inputs: exact explicit oracle and production guard checks."""
import copy
import hashlib
from pathlib import Path
import random
import subprocess
import sys
import unittest

import caps
import proof
import test_proof


def fixture(texts,banned=(),seed=(),D=7,rng=None):
    banned=set(banned);rng=rng or random.Random(6001);owners={}
    for (pid,i,j),word in proof.allowed(texts,banned).items():owners.setdefault(word,set()).add(pid)
    alphabet=sorted(set(''.join(texts.values()))|{'~'})
    pool=sorted(set(alphabet)|set(seed)|{word for word,pids in owners.items() if len(pids)>1})
    q=[rng.randrange(40) for pid,text in sorted(texts.items()) for i in range(len(text))
       for j in range(i+1,len(text)+1) if text[i:j] in pool]
    return dict(texts=texts,banned=banned,old_pool=pool,old_q=q,seed=list(seed),alphabet=alphabet,D=D,
        expected_source_hashes={pid:hashlib.sha256(text.encode()).hexdigest() for pid,text in texts.items()},
        expected_old_banned=banned)


def explicit(kw):
    texts,D=kw['texts'],kw['D'];values=iter(kw['old_q'])
    old={(pid,i,j):next(values) for pid,text in sorted(texts.items()) for i in range(len(text))
         for j in range(i+1,len(text)+1) if text[i:j] in kw['old_pool']}
    distances={}
    for pid,text in texts.items():
        d=[None]*len(text)+[0]
        for i in range(len(text)-1,-1,-1):
            d[i]=min(D*(9 if j-i==1 else -1)+old[pid,i,j]+d[j]
                     for j in range(i+1,len(text)+1) if (pid,i,j) in old)
        distances[pid]=d
    q={edge:max(0,distances[edge[0]][edge[1]]-distances[edge[0]][edge[2]]-
                   D*(9 if edge[2]-edge[1]==1 else -1)) for edge in proof.allowed(texts,kw['banned'])}
    return q,distances


class CapsTests(unittest.TestCase):
    def compare(self,kw,B=3,exhaustive=False):
        got=caps.check(**kw,capacity=B);q,d=explicit(kw)
        oracle=(test_proof.ProofTests().check(kw['texts'],kw['banned'],q,B,kw['D'])[0] if exhaustive else
                proof.certificate(kw['texts'],kw['banned'],q,B,kw['D']))
        self.assertEqual(got['all_caps'],oracle['all_caps'])
        self.assertEqual(got['all_prefix_schedule'],oracle['all_schedule_values'])
        self.assertEqual(got['local_shared_prefixes'],oracle['local_shared_prefixes'])
        self.assertEqual(got['base57']['base']['digests']['potentials_sha256'],caps.parent.digest(d))
        for actual,expected in zip(got['rows'],oracle['rows']):
            for key in ('k','charge','one_owner_slots','numerator','integer_lower_bound'):
                self.assertEqual(actual[key],expected[key],key)
        for actual,expected in zip(got['split_rows'],oracle['alternatives']):
            for key in ('one_owner_slots','shared_slots','joint_charge','prior57_charge','charge','allocation_choices'):
                self.assertEqual(actual[key],expected[key],key)
            self.assertEqual(actual['baseline'],sum(values[0] for values in expected['owner_functions'].values()))
        index=caps.parent.full.Index(kw['texts'],kw['banned']);identities={}
        for gid,group in enumerate(index.groups):
            pid,start=index.positions[group['lo']]
            for length in range(group['first'],group['last']+1):
                if length in group['excluded_lengths']:continue
                word=kw['texts'][pid][start:start+length]
                if oracle['support'][word] is None:identities[word]=(gid,length)
        for pid in kw['texts']:
            local=oracle['local_weights'][pid]
            expected=sorted(((local.get(word,0),*identity) for word,identity in identities.items()),
                            key=lambda row:(-row[0],row[1],row[2]))[:B]
            self.assertEqual(got['local_shared_top_entries'][pid],expected)
            self.assertEqual(got['local_shared_counts'][pid],{'available':len(identities),
                'occurring':sum(word in local for word in identities),
                'positive':sum(local.get(word,0)>0 for word in identities)})
        self.assertEqual(got['work']['schedule_occurrences_admitted'],len(q))
        self.assertEqual(got['work']['allocation_heap_pops'],sum(range(len(got['split_rows']))))
        self.assertLessEqual(got['work']['zero_identity_inspections'],2*B*len(kw['texts']))
        return got

    def test_random_oracle_and_finite_capacities(self):
        rng=random.Random(6017)
        for _ in range(12):
            texts={str(i):''.join(rng.choice('abcd') for _ in range(3)) for i in range(2)}
            kw=fixture(texts,set(texts.values()),rng=rng)
            self.compare(kw,3,True)
            for B in (0,1,8):self.compare(kw,B)

    def test_strict_fixed53_gain_and_integer_scaling(self):
        for D in (1,3):
            kw=fixture({'p':'abc','q':'abd'},{'abc','abd'},D=D)
            kw['old_q']=[19*D if j-i==2 else 0 for pid,text in sorted(kw['texts'].items())
                for i in range(len(text)) for j in range(i+1,len(text)+1) if text[i:j] in kw['old_pool']]
            got=self.compare(kw,3,True)
            self.assertEqual(got['base57']['rows'][2]['charge'],76*D)
            self.assertEqual(got['rows'][2]['charge'],38*D)
            self.assertEqual(got['rows'][2]['integer_lower_bound'],16)

    def test_shared_coupling_and_local_entry_outside_global_top(self):
        kw=fixture({'p':'ab','q':'ab'},{'ab'},D=1);kw['old_q']=[10,0,0,10]
        got=self.compare(kw,1,True)
        self.assertEqual(got['split_rows'][0]['baseline'],20)
        self.assertEqual(got['split_rows'][0]['joint_charge'],20)
        self.assertEqual(got['split_rows'][0]['prior57_charge'],10)
        self.assertNotEqual(got['local_shared_top_entries']['p'],got['local_shared_top_entries']['q'])
        global_top=got['base57']['base']['tightened']['top_entries'][2]
        self.assertTrue(any(rows[0][1:]!=global_top[0][1:] for rows in got['local_shared_top_entries'].values()))

    def test_repeats_bans_seed_and_locally_absent_zero_entries(self):
        self.compare(fixture({'10':'abcxabc','2':'abcyabc'},{'abc','abcxabc','abcyabc'},seed=['cx','~~']),7)
        self.compare(fixture({'p':'aaaa'},{'aaaa'},seed=['aaa','~~']),256)
        kw=fixture({'p':'ab','q':'ab','r':'cd'},{'ab','cd'});kw['old_q']=[0]*len(kw['old_q'])
        got=self.compare(kw,256)
        self.assertEqual(got['local_shared_counts']['r'],{'available':2,'occurring':0,'positive':0})
        self.assertEqual(len(got['local_shared_top_entries']['r']),2)

    def test_all_arc_schedule_not_truncated_to_top_entries(self):
        kw=fixture({'p':'aaaa'},{'aaaa'},seed=['aaa'],D=1)
        kw['old_q']=[4,10,4,10,4,4]
        got=self.compare(kw,1)
        self.assertEqual(got['all_caps']['p'],31)
        self.assertEqual(got['base57']['owner_top_entries']['p'][0][0],27)
        self.assertGreater(got['all_caps']['p'],got['base57']['owner_top_entries']['p'][0][0])

    def test_reject_wrong_authority_missing_shared_and_bad_q(self):
        kw=fixture({'p':'abc','q':'abd'},{'abc','abd'})
        for change in ({'expected_source_hashes':{}},{'expected_old_banned':set()},
                       {'expected_occurrence_sha256':'0'*64},{'old_q':kw['old_q']+[0]},
                       {'old_q':[True]+kw['old_q'][1:]},{'old_q':[-1]+kw['old_q'][1:]}):
            with self.assertRaises(AssertionError):caps.check(**(kw|change),capacity=3)
        bad=copy.deepcopy(kw);bad['old_pool'].remove('ab')
        bad['old_q']=[0 for pid,text in sorted(bad['texts'].items()) for i in range(len(text))
            for j in range(i+1,len(text)+1) if text[i:j] in bad['old_pool']]
        with self.assertRaisesRegex(AssertionError,'omits an allowed shared'):caps.check(**bad,capacity=3)

    def test_optimized_python_fails_closed(self):
        proc=subprocess.run([sys.executable,'-O','-B','-c',
            'import caps;caps.check({},set(),[],[],[],[],1,expected_source_hashes={},expected_old_banned=set())'],
            cwd=Path(__file__).resolve().parent,capture_output=True,text=True,timeout=5)
        self.assertNotEqual(proc.returncode,0);self.assertIn('normal assertions required',proc.stderr)

    def test_independent_checker_and_every_forward_recurrence(self):
        import independent
        rng=random.Random(6029)
        fixtures=[fixture({'p':'aaaa'},{'aaaa'},seed=['aaa','~~']),
                  fixture({'p':'ab','q':'ab','r':'cd'},{'ab','cd'})]
        fixtures += [fixture({str(i):''.join(rng.choice('abcd') for _ in range(4))
                             for i in range(3)},rng=rng) for _ in range(8)]
        for kw in fixtures:
            for B in (0,1,3,256):
                production=caps.check(**kw,capacity=B)
                replay=independent.check(**kw,capacity=B,
                    expected_base57_prefix_schedule=production['base57']['owner_prefix_schedule'],
                    expected_prefix_schedule=production['all_prefix_schedule'])
                for key in caps.COMMON_FIELDS:self.assertEqual(production[key],replay[key],key)
                self.assertEqual(caps.scientific57(production['base57']),caps.scientific57(replay['base57']))
                for key in production['digests'].keys()&replay['digests'].keys():
                    self.assertEqual(production['digests'][key],replay['digests'][key],key)
                self.assertTrue(replay['production_forward_schedule_checked'])
                self.assertEqual(production['digests']['all_prefix_schedule_sha256'],
                                 replay['production_forward_schedule_sha256'])


if __name__=='__main__':unittest.main()
