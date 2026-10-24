"""Independent exhaustive invented dictionary/path and allocation oracles."""
import itertools
from pathlib import Path
import random
import subprocess
import sys
import unittest
import proof as p


def paths(text,vocab):
    if not text:return [()]
    return [(word,)+rest for word in vocab if text.startswith(word)
            for rest in paths(text[len(word):],vocab)]


def interval_oracle(intervals):
    answer=0
    for mask in range(1<<len(intervals)):
        selected=sorted(intervals[i] for i in range(len(intervals)) if mask>>i&1)
        if all(a[1]<=b[0] for a,b in zip(selected,selected[1:])):
            answer=max(answer,sum(x[2] for x in selected))
    return answer


class ProofTests(unittest.TestCase):
    def check(self,texts,banned,q,B=3,D=1):
        c=p.certificate(texts,banned,q,B,D)
        words=sorted({t[i:j] for t in texts.values() for i in range(len(t))
                      for j in range(i+1,len(t)+1) if t[i:j] not in banned})
        owners={w:{pid for pid,t in texts.items() if w in t} for w in words}
        weights={w:sum(value for (pid,i,j),value in q.items() if texts[pid][i:j]==w) for w in words}
        self.assertEqual(c['weights'],weights)
        exact_L=0
        for pid,text in texts.items():
            costs=[]
            for sequence in paths(text,words):
                offset=0;cost=0
                for word in sequence:
                    end=offset+len(word)
                    cost+=D*(9 if len(word)==1 else -1)+q[pid,offset,end];offset=end
                costs.append(cost)
            exact_L+=min(costs)
        self.assertEqual(c['L'],exact_L)
        for pid,text in texts.items():
            intervals=[(i,j,q[pid,i,j]) for i in range(len(text)) for j in range(i+1,len(text)+1)
                       if text[i:j] in owners and owners[text[i:j]]=={pid}]
            self.assertEqual(c['owner_caps'][pid],interval_oracle(intervals))
            expected=[0]
            for w in sorted((w for w in words if owners[w]=={pid}),key=lambda w:(-weights[w],w))[:B]:
                expected.append(expected[-1]+weights[w])
            self.assertEqual(c['owner_prefixes'][pid],expected)
            clipped=c['capped_prefixes'][pid]
            differences=[b-a for a,b in zip(clipped,clipped[1:])]
            self.assertEqual(differences,sorted(differences,reverse=True))
        owner_ids=sorted(texts);prefixes=c['capped_prefixes']
        for j,value in enumerate(c['one_owner_prefix']):
            allocations=(a for a in itertools.product(*(range(len(prefixes[x])) for x in owner_ids)) if sum(a)==j)
            self.assertEqual(value,max(sum(prefixes[x][count] for x,count in zip(owner_ids,a)) for a in allocations))
        flattened=sorted((delta,pid,j) for pid,values in prefixes.items()
                         for j,delta in enumerate((b-a for a,b in zip(values,values[1:])),1))
        stable=sorted(flattened,key=lambda v:(-v[0],v[1],v[2]))[:B]
        self.assertEqual(c['marginal_choices'],[(pid,j,d) for d,pid,j in stable])
        shared=[weights[w] for w in words if len(owners[w])>=2]
        for row in c['rows']:
            charges=[]
            for a in itertools.product(*(range(len(prefixes[x])) for x in owner_ids)):
                j=sum(a)
                if j<=min(B,row['k']):
                    charges.append(sum(prefixes[x][count] for x,count in zip(owner_ids,a))+
                                   sum(sorted(shared,reverse=True)[:B-j]))
            self.assertEqual(row['charge'],max(charges))
        dictionary_count=path_count=0
        for size in range(min(B,len(words))+1):
            for dictionary in itertools.combinations(words,size):
                allpaths=[paths(t,dictionary) for t in texts.values()]
                if not all(allpaths):continue
                dictionary_count+=1;k=sum(len(owners[w])==1 for w in dictionary)
                row=c['rows'][k]
                # Every actual path, not merely a canonical or best-F encoding.
                for selected in itertools.product(*allpaths):
                    path_count+=1;F=0;Q=0;oneQ={pid:0 for pid in texts}
                    for pid,sequence in zip(texts,selected):
                        start=0
                        for w in sequence:
                            end=start+len(w);value=q[pid,start,end]
                            F+=9 if len(w)==1 else -1;Q+=value
                            if len(owners[w])==1:oneQ[pid]+=value
                            start=end
                    for pid,value in oneQ.items():
                        j=sum(owners[w]=={pid} for w in dictionary)
                        self.assertLessEqual(value,c['capped_prefixes'][pid][j])
                    self.assertLessEqual(Q,row['charge'])
                    self.assertLessEqual(c['L']-row['charge'],D*F)
                    self.assertLessEqual(row['integer_lower_bound'],F)
        return c,dictionary_count,path_count

    def test_cross_entry_overlap_strict_fixed53_penalties(self):
        texts={'p':'abc'};banned={'abc'};D=3
        # Old character-only q=0 gives d_i=9D*(n-i). This is exactly q53.
        d=[27,18,9,0]
        q={edge:max(0,D*(d[edge[1]]-d[edge[2]])-D*(9 if edge[2]-edge[1]==1 else -1))
           for edge in p.allowed(texts,banned)}
        c,nd,np=self.check(texts,banned,q,B=3,D=D)
        self.assertEqual(c['distances']['p'],[x*D for x in d])
        self.assertGreater(c['owner_prefixes']['p'][2],c['owner_caps']['p'])
        self.assertGreater(c['rows'][2]['old_charge'],c['rows'][2]['charge'])
        self.assertGreater(nd,0);self.assertGreater(np,0)

    def test_repeated_one_owner_overlap_and_no_truncated_schedule(self):
        texts={'p':'aaaa'};banned={'aaaa'}
        q={edge:10 if edge[2]-edge[1]>1 else 1 for edge in p.allowed(texts,banned)}
        c,_,_=self.check(texts,banned,q,B=1)
        self.assertEqual(c['weights']['aa'],30);self.assertEqual(c['owner_caps']['p'],20)
        self.assertEqual(c['rows'][1]['old_charge'],30);self.assertEqual(c['rows'][1]['charge'],20)
        # Top1 is aa; low-weight character occurrences are still part of R.
        texts={'p':'abc'};banned={'abc'}
        q={edge:10 if texts[edge[0]][edge[1]:edge[2]]=='ab' else 1 for edge in p.allowed(texts,banned)}
        c,_,_=self.check(texts,banned,q,B=1)
        self.assertEqual(c['owner_top_entries']['p'],['ab'])
        self.assertEqual(c['owner_caps']['p'],11)
        # A covering dictionary of size B=1 may need the omitted entry: top1
        # aaa has weight20 but schedule10, whereas {a} covers with penalty16.
        texts={'p':'aaaa'};banned={'aaaa'}
        q={edge:10 if edge[2]-edge[1]==3 else 4 if edge[2]-edge[1]==1 else 0
           for edge in p.allowed(texts,banned)}
        c,_,_=self.check(texts,banned,q,B=1)
        self.assertEqual(c['owner_top_entries']['p'],['aaa'])
        self.assertEqual(c['owner_caps']['p'],16)
        self.assertEqual(c['rows'][1]['charge'],16)

    def test_nonoverlap_no_change_zero_capacity_and_zero_ties(self):
        texts={'p':'ab'};banned={'ab'};q={('p',0,1):2,('p',1,2):3}
        for B in (0,1,2,5):
            c,_,_=self.check(texts,banned,q,B=B,D=2)
            self.assertTrue(all(row['charge']==row['old_charge'] for row in c['rows']))
        texts={'b':'xx','a':'yy'};banned={'xx','yy'}
        q={edge:0 for edge in p.allowed(texts,banned)}
        c,_,_=self.check(texts,banned,q,B=4)
        self.assertEqual(c['marginal_choices'],[('a',1,0),('b',1,0)])
        self.assertTrue(all(row['one_owner_slots']==0 for row in c['rows']))

    def test_shared_singletons_owner_ties_and_random_exhaustive(self):
        rng=random.Random(57)
        for _ in range(18):
            texts={str(i):''.join(rng.choice('abc') for _ in range(3)) for i in range(2)}
            banned=set(texts.values())
            q={edge:rng.randrange(6) for edge in p.allowed(texts,banned)}
            self.check(texts,banned,q,B=3,D=3)
        c,_,_=self.check({'a':'ab','b':'ac'},{'ab','ac'},
                        {('a',0,1):3,('a',1,2):2,('b',0,1):4,('b',1,2):2},B=3)
        self.assertIsNone(c['support']['a']);self.assertEqual(c['shared_prefix'],[0,7])

    def test_invalid_penalties_missing_occurrences_and_optimization(self):
        texts={'a':'ab'};banned={'ab'};q={('a',0,1):1,('a',1,2):0}
        for bad in ({('a',0,1):1},{**q,('a',1,2):-1},{**q,('a',1,2):True}):
            with self.assertRaises(AssertionError):p.certificate(texts,banned,bad)
        proc=subprocess.run([sys.executable,'-O','-c','import proof; proof.certificate({},set(),{})'],
                            cwd=Path(__file__).resolve().parent,capture_output=True,text=True,timeout=5)
        self.assertNotEqual(proc.returncode,0);self.assertIn('normal assertions required',proc.stderr)

if __name__=='__main__':unittest.main()
