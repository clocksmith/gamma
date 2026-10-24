"""Independent exhaustive owner allocations and every tiny covering path."""
import itertools
from pathlib import Path
import random
import subprocess
import sys
import unittest
import proof as p


def paths(text,vocab):
    if not text:return [()]
    return [(w,)+rest for w in vocab if text.startswith(w) for rest in paths(text[len(w):],vocab)]


def interval_max(intervals):
    answer=0
    for mask in range(1<<len(intervals)):
        selected=sorted(intervals[i] for i in range(len(intervals)) if mask>>i&1)
        if all(a[1]<=b[0] for a,b in zip(selected,selected[1:])):
            answer=max(answer,sum(row[2] for row in selected))
    return answer


class ProofTests(unittest.TestCase):
    def compare(self,texts,banned,q,B=3,D=1):
        result=p.certificate(texts,banned,q,B,D);base=result['base57']
        words=sorted({t[i:j] for t in texts.values() for i in range(len(t)) for j in range(i+1,len(t)+1) if t[i:j] not in banned})
        owners={w:{pid for pid,t in texts.items() if w in t} for w in words}
        shared=[w for w in words if len(owners[w])>=2]
        forced=sorted(pid for pid,text in texts.items() if not paths(text,shared))
        self.assertEqual(result['forced_owners'],forced)
        weights={w:sum(value for (pid,i,j),value in q.items() if texts[pid][i:j]==w) for w in words}
        prefixes={}
        for pid,text in texts.items():
            one=[w for w in words if owners[w]=={pid}]
            self.assertEqual(result['owner_entry_counts'][pid],len(one))
            intervals=[(i,j,q[pid,i,j]) for i in range(len(text)) for j in range(i+1,len(text)+1) if text[i:j] in one]
            cap=interval_max(intervals);self.assertEqual(base['owner_caps'][pid],cap)
            prefix=[0]
            for w in sorted(one,key=lambda w:(-weights[w],w))[:B]:prefix.append(prefix[-1]+weights[w])
            prefixes[pid]=[min(value,cap) for value in prefix]
        self.assertEqual(prefixes,base['capped_prefixes'])
        owner_ids=sorted(texts);required=set(forced)
        allocations=list(itertools.product(*(range(1 if pid in required else 0,len(prefixes[pid])) for pid in owner_ids)))
        for j,value in result['required_owner_prefix'].items():
            exact=[sum(prefixes[pid][n] for pid,n in zip(owner_ids,counts)) for counts in allocations if sum(counts)==j]
            upto=[sum(prefixes[pid][n] for pid,n in zip(owner_ids,counts)) for counts in allocations if sum(counts)<=j]
            self.assertEqual(value,max(exact));self.assertEqual(value,max(upto))
        for row in result['rows']:
            if row['k']<len(forced):
                self.assertTrue(row['empty_by_required_owners'])
                self.assertIsNone(row['charge']);self.assertIsNone(row['integer_lower_bound']);continue
            options=[]
            for counts in allocations:
                j=sum(counts)
                if j<=min(B,row['k']):
                    charge=sum(prefixes[pid][n] for pid,n in zip(owner_ids,counts))+sum(sorted((weights[w] for w in shared),reverse=True)[:B-j])
                    options.append((charge,-j))
            expected,j=max(options)
            self.assertEqual(row['charge'],expected);self.assertEqual(row['one_owner_slots'],-j)
            self.assertLessEqual(row['charge'],base['rows'][row['k']]['charge'])
        covered=[];path_count=0
        for size in range(min(B,len(words))+1):
            for dictionary in itertools.combinations(words,size):
                allpaths=[paths(t,dictionary) for t in texts.values()]
                if not all(allpaths):continue
                k=sum(len(owners[w])==1 for w in dictionary);covered.append((dictionary,k))
                self.assertGreaterEqual(k,len(forced))
                self.assertTrue(all(any(owners[w]=={pid} for w in dictionary) for pid in forced))
                for selected in itertools.product(*allpaths):
                    path_count+=1;Q=F=0
                    for pid,sequence in zip(texts,selected):
                        start=0
                        for word in sequence:
                            end=start+len(word);Q+=q[pid,start,end];F+=9 if len(word)==1 else -1;start=end
                    self.assertLessEqual(base['L'],D*F+Q)
                    for row in result['rows'][k:]:
                        self.assertFalse(row['empty_by_required_owners'])
                        self.assertLessEqual(Q,row['charge'])
                        self.assertLessEqual(row['numerator'],D*F)
                        self.assertLessEqual(row['integer_lower_bound'],F)
        return result,covered,path_count

    def test_fixed_q53_strict_gain_at_minimum_feasible_budget(self):
        texts={'p':'abba','q':'cc','r':'aa'};banned=set(texts.values())
        # Original character-only graph, old q=0: d_i=9*(n-i), D=1.
        q={edge:0 if edge[2]-edge[1]==1 else 9*(edge[2]-edge[1])+1 for edge in p.parent.allowed(texts,banned)}
        got,covered,npaths=self.compare(texts,banned,q,B=3)
        self.assertEqual(got['forced_owners'],['p','q'])
        self.assertEqual(min(k for _,k in covered),2)
        self.assertIn((('a','b','c'),2),covered);self.assertGreater(npaths,0)
        self.assertEqual(got['base57']['rows'][2]['charge'],38)
        self.assertEqual(got['rows'][2]['charge'],28)
        self.assertEqual(got['rows'][2]['integer_lower_bound']-got['base57']['rows'][2]['integer_lower_bound'],10)
        self.assertEqual(got['rows'][3]['charge'],got['base57']['rows'][3]['charge'])
        self.assertEqual(got['base57']['distances'],{pid:[9*(len(t)-i) for i in range(len(t)+1)] for pid,t in texts.items()})

    def test_general_forced_owners_not_private_characters(self):
        texts={'p':'ab','q':'ba'};banned={'a','b'}
        q={edge:3 for edge in p.parent.allowed(texts,banned)}
        got,covered,_=self.compare(texts,banned,q,B=2)
        self.assertEqual(got['forced_owners'],['p','q'])
        self.assertTrue(all(sum(ch in text for text in texts.values())==2 for ch in 'ab'))
        self.assertEqual(min(k for _,k in covered),2)

    def test_null_no_forced_and_zero_marginals(self):
        for texts,banned in (({'p':'ab','q':'ab'},{'ab'}),({'p':'aa','q':'bb'},{'aa','bb'})):
            q={edge:0 for edge in p.parent.allowed(texts,banned)}
            got,_,_=self.compare(texts,banned,q,B=4)
            for row in got['rows']:
                if not row['empty_by_required_owners']:self.assertEqual(row['charge'],got['base57']['rows'][row['k']]['charge'])
        self.assertEqual(got['remaining_marginal_choices'],[])
        got,_,_=self.compare({'p':'ab','q':'ab'},{'ab'},
            {edge:7 for edge in p.parent.allowed({'p':'ab','q':'ab'},{'ab'})},B=3)
        self.assertEqual(got['coverage_floor'],0)
        self.assertEqual([r['charge'] for r in got['rows']],[r['charge'] for r in got['base57']['rows']])

    def test_capacity_empty_and_non_sufficiency(self):
        texts={'p':'ab','q':'cd'};banned=set(texts.values());q={edge:1 for edge in p.parent.allowed(texts,banned)}
        for B in (0,1,2,5):
            got,covered,_=self.compare(texts,banned,q,B)
            self.assertEqual(got['coverage_floor'],2)
            if B<2:self.assertTrue(all(r['empty_by_required_owners'] for r in got['rows']))
            if B==2:
                self.assertFalse(got['rows'][2]['empty_by_required_owners']);self.assertEqual(covered,[])
            if B==5:self.assertEqual(min(k for _,k in covered),4)

    def test_random_full_weak_duality_and_exact_allocation(self):
        rng=random.Random(61)
        for _ in range(24):
            texts={str(i):''.join(rng.choice('abc') for _ in range(3)) for i in range(2)}
            banned=set(texts.values());q={edge:rng.randrange(12) for edge in p.parent.allowed(texts,banned)}
            self.compare(texts,banned,q,B=3,D=3)
        prefix={'a':[0,4,8,8],'b':[0,0,0],'c':[0,4,8]}
        totals,choices,base=p.required_allocation(prefix,['b'],5)
        self.assertEqual(base,0);self.assertEqual(totals,{1:0,2:4,3:8,4:12,5:16})
        self.assertEqual(choices,[('a',1,4),('a',2,4),('c',1,4),('c',2,4)])

    def test_invalid_and_optimization_fail_closed(self):
        texts={'p':'aa'};banned={'aa'};q={edge:0 for edge in p.parent.allowed(texts,banned)}
        for value in (-1,True,.5):
            bad=dict(q);bad[next(iter(bad))]=value
            with self.assertRaises(AssertionError):p.certificate(texts,banned,bad)
        with self.assertRaises(AssertionError):p.certificate({'p':'a'},{'a'},{})
        with self.assertRaises(AssertionError):p.required_allocation({'p':[0]},['p'],1)
        with self.assertRaises(AssertionError):p.required_allocation({'p':[0,1,3]},[],2)
        proc=subprocess.run([sys.executable,'-O','-B','-c','import proof; proof.certificate({},set(),{})'],
                            cwd=Path(__file__).resolve().parent,capture_output=True,text=True,timeout=5)
        self.assertNotEqual(proc.returncode,0);self.assertIn('normal assertions required',proc.stderr)


if __name__=='__main__':unittest.main()
