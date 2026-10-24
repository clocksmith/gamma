"""Exhaustive tiny dictionaries, all paths, interval sets and owner allocations."""
import itertools
from pathlib import Path
import random
import subprocess
import sys
import unittest
import proof as p


def paths(text,words):
    if not text:return [()]
    return [(word,)+rest for word in words if text.startswith(word) for rest in paths(text[len(word):],words)]


def interval_max(arcs):
    best=0
    for size in range(len(arcs)+1):
        for subset in itertools.combinations(arcs,size):
            ordered=sorted(subset)
            if all(a[1]<=b[0] for a,b in zip(ordered,ordered[1:])):best=max(best,sum(v for _,_,v in subset))
    return best


class ProofTests(unittest.TestCase):
    def compare(self,texts,banned,q,B=3,D=1):
        got=p.certificate(texts,banned,q,B,D);base=got['base60']
        words=sorted({text[i:j] for text in texts.values() for i in range(len(text))
                      for j in range(i+1,len(text)+1) if text[i:j] not in banned})
        owners={word:{pid for pid,text in texts.items() if word in text} for word in words}
        shared=[word for word in words if len(owners[word])>1]
        forced=sorted(pid for pid,text in texts.items() if not paths(text,shared))
        self.assertEqual(got['forced_owners'],forced)
        local={pid:{word:sum(q[pid,i,j] for i in range(len(text)) for j in range(i+1,len(text)+1)
                             if text[i:j]==word) for word in words} for pid,text in texts.items()}
        weights={word:sum(local[pid][word] for pid in texts) for word in words}
        A={};Rall={};Rone={};L=0
        for pid,text in texts.items():
            one=[word for word in words if owners[word]=={pid}]
            prefix=[0]
            for value in sorted((weights[word] for word in one),reverse=True)[:B]:prefix.append(prefix[-1]+value)
            A[pid]=prefix
            arcs=[(i,j,q[pid,i,j]) for i in range(len(text)) for j in range(i+1,len(text)+1) if text[i:j] in owners]
            Rall[pid]=interval_max(arcs)
            Rone[pid]=interval_max([(i,j,value) for i,j,value in arcs if owners[text[i:j]]=={pid}])
            costs=[]
            for sequence in paths(text,words):
                at=0;value=0
                for word in sequence:value+=D*(9 if len(word)==1 else -1)+q[pid,at,at+len(word)];at+=len(word)
                costs.append(value)
            L+=min(costs)
        self.assertEqual(base['L'],L);self.assertEqual(base['owner_prefixes'],A)
        self.assertEqual(base['all_caps'],Rall);self.assertEqual(base['one_owner_caps'],Rone)
        ids=sorted(texts);required=set(forced)
        allocations=list(itertools.product(*(range(int(pid in required),len(A[pid])) for pid in ids)))
        for row in got['split_rows']:
            j=row['one_owner_slots'];s=B-j
            Sp={pid:sum(sorted((local[pid][word] for word in shared),reverse=True)[:s]) for pid in ids}
            feasible=[ts for ts in allocations if sum(ts)==j]
            upto=[ts for ts in allocations if sum(ts)<=j]
            objective=lambda ts:sum(min(Sp[pid]+A[pid][t],Rall[pid]) for pid,t in zip(ids,ts))
            expected=max(map(objective,feasible));self.assertEqual(expected,max(map(objective,upto)))
            prior=max(sum(min(A[pid][t],Rone[pid]) for pid,t in zip(ids,ts)) for ts in feasible)
            prior+=sum(sorted((weights[word] for word in shared),reverse=True)[:s])
            self.assertEqual(row['joint_charge'],expected);self.assertEqual(row['prior61_charge'],prior)
            self.assertEqual(row['charge'],min(expected,prior))
            alloc=row['allocation']
            self.assertEqual(alloc['zero_baseline'],sum(min(Sp[pid],Rall[pid]) for pid in ids))
            self.assertEqual(alloc['mandatory_baseline'],sum(min(Sp[pid]+A[pid][int(pid in required)],Rall[pid]) for pid in ids))
            self.assertEqual(alloc['charge'],objective(tuple(alloc['allocation'][pid] for pid in ids)))
            marginals=[(values[rank]-values[rank-1],pid,rank) for pid,values in row['owner_functions'].items()
                       for rank in range(2 if pid in required else 1,len(values))]
            ordered=sorted(marginals,key=lambda value:(-value[0],value[1],value[2]))[:j-len(forced)]
            self.assertEqual(alloc['residual_choices'],[(pid,rank,value) for value,pid,rank in ordered])
        previous=-1
        for row in got['rows']:
            if row['k']<len(forced):
                self.assertTrue(row['empty_by_required_owners']);self.assertIsNone(row['charge']);self.assertIsNone(row['integer_lower_bound']);continue
            selected=max((split for split in got['split_rows'] if split['one_owner_slots']<=row['k']),key=lambda split:(split['charge'],-split['one_owner_slots']))
            self.assertEqual(row['charge'],selected['charge']);self.assertEqual(row['one_owner_slots'],selected['one_owner_slots'])
            self.assertGreaterEqual(row['charge'],previous);previous=row['charge']
            self.assertLessEqual(row['charge'],base['rows'][row['k']]['charge'])
            self.assertLessEqual(row['charge'],got['base61']['rows'][row['k']]['charge'])
            self.assertEqual(row['integer_lower_bound'],-(-row['numerator']//D))
        covering=[];npaths=0
        for size in range(min(B,len(words))+1):
            for dictionary in itertools.combinations(words,size):
                per_source=[paths(text,dictionary) for text in texts.values()]
                if not all(per_source):continue
                j=sum(len(owners[word])==1 for word in dictionary);covering.append((dictionary,j))
                self.assertGreaterEqual(j,len(forced))
                for choice in itertools.product(*per_source):
                    npaths+=1;Q=F=0
                    for pid,sequence in zip(texts,choice):
                        at=0
                        for word in sequence:Q+=q[pid,at,at+len(word)];F+=9 if len(word)==1 else -1;at+=len(word)
                    self.assertLessEqual(L,D*F+Q)
                    for row in got['rows'][j:]:
                        self.assertFalse(row['empty_by_required_owners']);self.assertLessEqual(Q,row['charge'])
                        self.assertLessEqual(row['numerator'],D*F);self.assertLessEqual(row['integer_lower_bound'],F)
        return got,covering,npaths

    def test_strict_fixed_q53_gain_against_both_components(self):
        texts={'p':'abc','q':'abd','u':'xyyx','v':'zz','w':'xx'};banned=set(texts.values())
        for D in (1,3):
            q={e:0 if e[2]-e[1]==1 else (9*(e[2]-e[1])+1)*D for e in p.joint.allowed(texts,banned)}
            got,covering,npaths=self.compare(texts,banned,q,B=6,D=D)
            self.assertEqual(got['forced_owners'],['p','q','u','v'])
            self.assertIn((('a','bc','bd','x','y','z'),4),covering);self.assertGreater(npaths,0)
            self.assertEqual(got['base60']['rows'][4]['charge'],76*D)
            self.assertEqual(got['base61']['rows'][4]['charge'],104*D)
            self.assertEqual(got['rows'][4]['charge'],66*D)
            self.assertEqual(got['rows'][4]['integer_lower_bound'],60)
            self.assertEqual(got['base60']['distances'],{pid:[9*D*(len(text)-i) for i in range(len(text)+1)] for pid,text in texts.items()})

    def test_mandatory_joint_baseline_not_added_as_owner_only_cost(self):
        # A forced first slot may be fully saturated by shared contribution.
        result=p.allocate({'a':[7,7,7],'b':[3,8,10]},['a'],3)
        self.assertEqual(result['zero_baseline'],10);self.assertEqual(result['mandatory_baseline'],10)
        self.assertEqual(result['mandatory_increment'],0);self.assertEqual(result['charge'],17)
        self.assertEqual(result['residual_choices'],[('b',1,5),('b',2,2)])
        tied=p.allocate({'b':[5,5,5],'a':[7,7,7]},['b'],3)
        self.assertEqual(tied['charge'],12);self.assertEqual(tied['residual_choices'],[('a',1,0),('a',2,0)])

    def test_forced_by_bans_without_private_characters(self):
        texts={'p':'ab','q':'ba'};banned={'a','b'}
        got,covering,_=self.compare(texts,banned,{e:3 for e in p.joint.allowed(texts,banned)},B=2)
        self.assertEqual(got['forced_owners'],['p','q']);self.assertTrue(covering)

    def test_no_forced_zero_caps_and_non_sufficient_floor(self):
        for B in (0,1,3,5):
            texts={'p':'ab','q':'ab'};banned={'ab'}
            got,_,_=self.compare(texts,banned,{e:0 for e in p.joint.allowed(texts,banned)},B=B)
            self.assertEqual(got['coverage_floor'],0)
            self.assertEqual([row['charge'] for row in got['rows']],[row['charge'] for row in got['base60']['rows']])
        texts={'p':'ab','q':'cd'};banned=set(texts.values());q={e:1 for e in p.joint.allowed(texts,banned)}
        for B in (0,1,2,5):
            got,covering,_=self.compare(texts,banned,q,B)
            if B<2:self.assertTrue(all(row['empty_by_required_owners'] for row in got['rows']))
            if B==2:self.assertFalse(got['rows'][2]['empty_by_required_owners']);self.assertEqual(covering,[])

    def test_random_exhaustive_paths_intervals_allocations(self):
        rng=random.Random(62)
        for _ in range(24):
            texts={str(i):''.join(rng.choice('abc') for _ in range(3)) for i in range(2)};banned=set(texts.values())
            q={e:rng.randrange(12) for e in p.joint.allowed(texts,banned)}
            self.compare(texts,banned,q,B=3,D=3)

    def test_invalid_and_optimized_python_fail_closed(self):
        texts={'p':'aa'};banned={'aa'};q={e:0 for e in p.joint.allowed(texts,banned)}
        for value in (-1,True,.5):
            bad=dict(q);bad[next(iter(bad))]=value
            with self.assertRaises(AssertionError):p.certificate(texts,banned,bad)
        with self.assertRaises(AssertionError):p.certificate({'p':'a'},{'a'},{})
        with self.assertRaises(AssertionError):p.allocate({'p':[0]},['p'],1)
        with self.assertRaises(AssertionError):p.allocate({'p':[3,4,6]},[],2)
        self.assertIsNone(p.allocate({'p':[0,1]},['p'],0))
        proc=subprocess.run([sys.executable,'-O','-B','-c','import proof;proof.certificate({},set(),{})'],
            cwd=Path(__file__).resolve().parent,capture_output=True,text=True,timeout=5)
        self.assertNotEqual(proc.returncode,0);self.assertIn('normal assertions required',proc.stderr)


if __name__=='__main__':unittest.main()
