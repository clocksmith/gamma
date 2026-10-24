"""Every tiny allocation, covering dictionary, joint path and price schedule."""
import itertools
from pathlib import Path
import random
import subprocess
import sys
import unittest
import proof as p


def paths(text,words):
    if not text:return [()]
    return [(word,)+tail for word in words if text.startswith(word)
            for tail in paths(text[len(word):],words)]


def schedules(intervals):
    yield []
    ordered=sorted(intervals)
    for index,first in enumerate(ordered):
        for tail in schedules([arc for arc in ordered[index+1:] if arc[0]>=first[1]]):yield [first]+tail


class ProofTests(unittest.TestCase):
    def check(self,texts,banned,q,prices,B=3,D=1):
        result=p.certificate(texts,banned,q,prices,B,D);base=result['base61']['base57']
        edges={(pid,i,j):text[i:j] for pid,text in texts.items() for i in range(len(text))
               for j in range(i+1,len(text)+1) if text[i:j] not in banned}
        words=sorted(set(edges.values()));owners={w:{pid for (pid,i,j),word in edges.items() if word==w} for w in words}
        counts={word:sum(w==word for w in edges.values()) for word in words}
        weights={word:sum(q[e] for e,w in edges.items() if w==word) for word in words}
        shared=[w for w in words if len(owners[w])>=2]
        forced=sorted(pid for pid,text in texts.items() if not paths(text,shared))
        self.assertEqual(result['forced_owners'],forced);self.assertEqual(result['coverage_floor'],len(forced))
        prefixes={}
        for pid,text in texts.items():
            one=[w for w in words if owners[w]=={pid}]
            intervals=[(i,j,w,q[pid,i,j]) for (source,i,j),w in edges.items() if source==pid and w in one]
            all_schedules=list(schedules(intervals));caps=[]
            for price in prices:
                cap=max(sum(max(v-price//counts[w],0) for _,_,w,v in schedule) for schedule in all_schedules)
                caps.append(cap);self.assertEqual(result['base63']['price_caps'][pid][price],cap)
            A=[0]
            for weight in sorted((weights[w] for w in one),reverse=True)[:B]:A.append(A[-1]+weight)
            prefixes[pid]=[min(value,min(price*t+cap for price,cap in zip(prices,caps))) for t,value in enumerate(A)]
        self.assertEqual(prefixes,result['base63']['priced_prefixes'])
        ids=sorted(texts);mandatory=set(forced)
        allocations=list(itertools.product(*(range(int(pid in mandatory),len(prefixes[pid])) for pid in ids)))
        for j,value in result['required_priced_prefix'].items():
            possibilities=[sum(prefixes[pid][count] for pid,count in zip(ids,counts))
                           for counts in allocations if sum(counts)==j]
            self.assertEqual(value,max(possibilities))
        if len(forced)<=B:self.assertEqual(result['mandatory_value'],sum(prefixes[pid][1] for pid in forced))
        previous=None
        for row in result['rows']:
            if row['k']<len(forced):
                self.assertTrue(row['empty_by_required_owners'])
                self.assertTrue(all(value is None for key,value in row.items() if key not in ('k','empty_by_required_owners')))
                continue
            candidates=[]
            for allocation in allocations:
                j=sum(allocation)
                if j<=min(row['k'],B):
                    charge=sum(prefixes[pid][count] for pid,count in zip(ids,allocation))+sum(sorted((weights[w] for w in shared),reverse=True)[:B-j])
                    candidates.append((charge,-j))
            charge,negj=max(candidates)
            self.assertEqual(row['charge'],charge);self.assertEqual(row['one_owner_slots'],-negj)
            self.assertEqual(row['shared_slots'],min(B+negj,len(shared)))
            self.assertEqual(row['numerator'],base['L']-charge)
            self.assertEqual(row['integer_lower_bound'],-(-row['numerator']//D))
            c61=result['base61']['rows'][row['k']]['charge'];c63=result['base63']['rows'][row['k']]['charge']
            self.assertEqual(row['charge_reduction_vs61'],c61-charge)
            self.assertEqual(row['charge_reduction_vs63'],c63-charge)
            self.assertEqual(row['charge_reduction_vs_min61_63'],min(c61,c63)-charge)
            self.assertLessEqual(charge,min(c61,c63))
            if previous is not None:self.assertGreaterEqual(charge,previous)
            previous=charge
        # Independent unrestricted complete paths establish original L.
        L=0
        for pid,text in texts.items():
            costs=[]
            for sequence in paths(text,words):
                pos=0;value=0
                for word in sequence:
                    end=pos+len(word);value+=D*(9 if len(word)==1 else -1)+q[pid,pos,end];pos=end
                costs.append(value)
            L+=min(costs)
        self.assertEqual(base['L'],L)
        covered=[];joint_paths=0
        for size in range(min(B,len(words))+1):
            for dictionary in itertools.combinations(words,size):
                alternatives=[paths(text,dictionary) for text in texts.values()]
                if not all(alternatives):continue
                k=sum(len(owners[w])==1 for w in dictionary);covered.append((dictionary,k))
                self.assertGreaterEqual(k,len(forced))
                self.assertTrue(all(any(owners[w]=={pid} for w in dictionary) for pid in forced))
                for selected in itertools.product(*alternatives):
                    Q=F=0;joint_paths+=1
                    for pid,sequence in zip(texts,selected):
                        pos=0
                        for word in sequence:
                            end=pos+len(word);Q+=q[pid,pos,end];F+=9 if len(word)==1 else -1;pos=end
                    for row in result['rows'][k:]:
                        self.assertFalse(row['empty_by_required_owners']);self.assertLessEqual(Q,row['charge'])
                        self.assertLessEqual(row['numerator'],D*F);self.assertLessEqual(row['integer_lower_bound'],F)
        return result,covered,joint_paths

    def test_strict_both_at_minimum_feasible_k_mandatory_zero_slot(self):
        texts={'p':'aaabXY','s':'aXb','z':'zz'};banned=set(texts.values())
        q={edge:10 if edge[0]=='p' and word in ('aa','ab','bX') else 0 for edge,word in p.priced.parent.allowed(texts,banned).items()}
        result,covered,np=self.check(texts,banned,q,[0,6],B=5)
        self.assertEqual(result['forced_owners'],['p','z']);self.assertEqual(min(k for _,k in covered),2)
        self.assertIn((tuple(sorted(('a','b','X','Y','z'))),2),covered);self.assertGreater(np,0)
        self.assertEqual(result['base63']['priced_prefixes']['p'][1:3],[17,20])
        self.assertEqual(result['base63']['priced_prefixes']['z'][1],0)
        self.assertEqual(result['mandatory_value'],17)
        self.assertEqual(result['base61']['rows'][2]['charge'],20)
        self.assertEqual(result['base63']['rows'][2]['charge'],20)
        self.assertEqual(result['rows'][2]['charge'],17)
        self.assertEqual(result['rows'][2]['one_owner_slots'],2)
        self.assertEqual(result['rows'][2]['charge_reduction_vs_min61_63'],3)
        self.assertEqual(result['rows'][2]['integer_lower_bound']-max(result['base61']['rows'][2]['integer_lower_bound'],result['base63']['rows'][2]['integer_lower_bound']),3)

    def test_strict_both_with_nonzero_mandatory_value(self):
        texts={'p':'aaabX','s':'aXb','z':'zz'};banned=set(texts.values())
        q={edge:10 if edge[0]=='p' and word in ('aa','ab','bX') else 1 if word=='z' else 0
           for edge,word in p.priced.parent.allowed(texts,banned).items()}
        result,covered,np=self.check(texts,banned,q,[0,6],B=4,D=3)
        self.assertEqual(result['forced_owners'],['z']);self.assertEqual(result['mandatory_value'],2)
        self.assertIn((tuple(sorted(('a','b','X','z'))),1),covered);self.assertGreater(np,0)
        self.assertEqual([result['base61']['rows'][2]['charge'],result['base63']['rows'][2]['charge'],result['rows'][2]['charge']],[22,20,19])

    def test_null_single_price_no_forced_and_general_banned_singletons(self):
        for texts,banned in (({'p':'ab','q':'ab'},{'ab'}),({'p':'aa','q':'bb'},{'aa','bb'})):
            q={edge:0 for edge in p.priced.parent.allowed(texts,banned)}
            result,_,_=self.check(texts,banned,q,[0,2],B=4)
            for row in result['rows']:
                if not row['empty_by_required_owners']:self.assertEqual(row['charge'],result['base61']['rows'][row['k']]['charge'])
        texts={'p':'ab','q':'ba'};banned={'a','b'};q={edge:3 for edge in p.priced.parent.allowed(texts,banned)}
        result,covered,_=self.check(texts,banned,q,[0,4],B=2)
        self.assertEqual(result['forced_owners'],['p','q']);self.assertEqual(min(k for _,k in covered),2)
        # All characters are shared; the general condition is shared reachability.
        self.assertTrue(all(sum(ch in text for text in texts.values())==2 for ch in 'ab'))
        result,_,_=self.check(texts,banned,q,[0],B=2)
        self.assertEqual(result['rows'][2]['charge'],result['base61']['rows'][2]['charge'])

    def test_empty_capacity_and_floor_not_sufficient(self):
        texts={'p':'ab','q':'cd'};banned=set(texts.values());q={edge:1 for edge in p.priced.parent.allowed(texts,banned)}
        for B in (0,1,2,4):
            result,covered,_=self.check(texts,banned,q,[0,2],B=B)
            self.assertEqual(result['coverage_floor'],2)
            if B<2:self.assertTrue(all(row['empty_by_required_owners'] for row in result['rows']))
            if B==2:self.assertFalse(result['rows'][2]['empty_by_required_owners']);self.assertEqual(covered,[])
            if B==4:self.assertTrue(covered)

    def test_random_exact_allocations_joint_paths_and_negative_ceilings(self):
        rng=random.Random(6801);negative=False
        for _ in range(16):
            texts={str(i):''.join(rng.choice('abc') for _ in range(3)) for i in range(2)}
            banned=set(texts.values());q={edge:rng.randrange(20) for edge in p.priced.parent.allowed(texts,banned)}
            result,_,_=self.check(texts,banned,q,[0,1,4,11],B=3,D=3)
            negative|=any(row['numerator'] is not None and row['numerator']<0 and row['numerator']%3 for row in result['rows'])
        self.assertTrue(negative)

    def test_invalid_bool_missing_banned_overlap_and_optimization(self):
        texts={'p':'aa'};banned={'aa'};q={edge:0 for edge in p.priced.parent.allowed(texts,banned)}
        self.assertEqual(p.certificate(texts,iter(banned),q,[0]),p.certificate(texts,banned,q,[0]))
        for prices in ([],[1],[0,-1],[0,True],[0,0],[1,0]):
            with self.assertRaises(AssertionError):p.certificate(texts,banned,q,prices)
        for bad in ({}, {**q,('p',0,2):0}, {('p',False,1):0,('p',1,2):0}, {**q,('p',1,2):True}, {**q,('p',1,2):-1}):
            with self.assertRaises(AssertionError):p.certificate(texts,banned,bad,[0])
        for B,D in ((True,1),(-1,1),(1,True),(1,0)):
            with self.assertRaises(AssertionError):p.certificate(texts,banned,q,[0],B,D)
        proc=subprocess.run([sys.executable,'-O','-B','-c','import proof;proof.certificate({},set(),{},[0])'],
            cwd=Path(__file__).resolve().parent,capture_output=True,timeout=5)
        self.assertNotEqual(proc.returncode,0);self.assertIn(b'normal assertions required',proc.stderr)

if __name__=='__main__':unittest.main()
