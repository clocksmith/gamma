"""Independent exhaustive tiny interval, dictionary, path and allocation checks."""
import itertools
from pathlib import Path
import random
import subprocess
import sys
import unittest
import proof as p


def paths(text,words):
    if not text:return [()]
    return [(w,)+rest for w in words if text.startswith(w) for rest in paths(text[len(w):],words)]


def schedules(intervals):
    for mask in range(1<<len(intervals)):
        selected=sorted(intervals[i] for i in range(len(intervals)) if mask>>i&1)
        if all(a[1]<=b[0] for a,b in zip(selected,selected[1:])):yield selected


class ProofTests(unittest.TestCase):
    def check(self,texts,banned,q,prices,B=3,D=1):
        c=p.certificate(texts,banned,q,prices,B,D);base=c['base57']
        edges={(pid,i,j):t[i:j] for pid,t in texts.items() for i in range(len(t)) for j in range(i+1,len(t)+1) if t[i:j] not in banned}
        words=sorted(set(edges.values()));owners={w:{pid for (pid,i,j),v in edges.items() if v==w} for w in words}
        counts={w:sum(v==w for v in edges.values()) for w in words if len(owners[w])==1}
        self.assertEqual(c['entry_occurrence_counts'],counts)
        weights={w:sum(q[e] for e,v in edges.items() if v==w) for w in words}
        self.assertEqual(base['weights'],weights)
        for pid,text in texts.items():
            intervals=[(i,j,w,q[pid,i,j]) for (source,i,j),w in edges.items() if source==pid and owners[w]=={pid}]
            chosen=list(schedules(intervals))
            for price in prices:
                residual=lambda w,v:max(v-price//counts[w],0)
                exact=max(sum(residual(w,v) for _,_,w,v in path) for path in chosen)
                self.assertEqual(c['price_caps'][pid][price],exact)
                for path in chosen:
                    distinct=len({w for _,_,w,_ in path});total=sum(v for _,_,_,v in path)
                    remains=sum(residual(w,v) for _,_,w,v in path)
                    self.assertLessEqual(total-remains,price*distinct)
                    self.assertLessEqual(total,price*distinct+exact)
                    if distinct<len(c['priced_prefixes'][pid]):self.assertLessEqual(total,c['priced_prefixes'][pid][distinct])
            vals=c['priced_prefixes'][pid];increments=[b-a for a,b in zip(vals,vals[1:])]
            self.assertTrue(all(v>=0 for v in increments));self.assertEqual(increments,sorted(increments,reverse=True))
        prefixes=c['priced_prefixes'];ids=sorted(prefixes)
        for j,value in enumerate(c['one_owner_prefix']):
            allocations=[a for a in itertools.product(*(range(len(prefixes[pid])) for pid in ids)) if sum(a)==j]
            self.assertEqual(value,max(sum(prefixes[pid][n] for pid,n in zip(ids,a)) for a in allocations))
        shared=sorted((weights[w] for w in words if len(owners[w])>=2),reverse=True)
        for row in c['rows']:
            choices=[]
            for allocation in itertools.product(*(range(len(prefixes[pid])) for pid in ids)):
                j=sum(allocation)
                if j<=min(row['k'],B):choices.append(sum(prefixes[pid][n] for pid,n in zip(ids,allocation))+sum(shared[:B-j]))
            self.assertEqual(row['charge'],max(choices))
            self.assertLessEqual(row['charge'],base['rows'][row['k']]['charge'])
        fullL=0
        for pid,text in texts.items():
            costs=[]
            for sequence in paths(text,words):
                start=0;cost=0
                for w in sequence:
                    end=start+len(w);cost+=D*(9 if len(w)==1 else -1)+q[pid,start,end];start=end
                costs.append(cost)
            fullL+=min(costs)
        self.assertEqual(base['L'],fullL)
        dictionaries=path_count=0
        for size in range(min(B,len(words))+1):
            for dictionary in itertools.combinations(words,size):
                alternatives=[paths(text,dictionary) for text in texts.values()]
                if not all(alternatives):continue
                dictionaries+=1;k=sum(len(owners[w])==1 for w in dictionary);row=c['rows'][k]
                for selected in itertools.product(*alternatives):
                    path_count+=1;Q=F=0;one=dict.fromkeys(texts,0)
                    for pid,sequence in zip(texts,selected):
                        start=0
                        for w in sequence:
                            end=start+len(w);value=q[pid,start,end];Q+=value;F+=9 if len(w)==1 else -1
                            if len(owners[w])==1:one[pid]+=value
                            start=end
                    for pid,value in one.items():
                        t=sum(owners[w]=={pid} for w in dictionary)
                        self.assertLessEqual(value,c['priced_prefixes'][pid][t])
                    self.assertLessEqual(Q,row['charge']);self.assertLessEqual(base['L']-row['charge'],D*F)
                    self.assertLessEqual(row['integer_lower_bound'],F)
        return c,dictionaries,path_count

    def test_strict_gain_in_coverable_class_general_fixed_q(self):
        texts={'p':'aaabX','s':'aXb'};banned=set(texts.values())
        q={e:10 if w in ('aa','ab','bX') else 0 for e,w in p.parent.allowed(texts,banned).items()}
        c,nd,np=self.check(texts,banned,q,[0,6],B=4)
        self.assertGreater(nd,0);self.assertGreater(np,0)
        self.assertEqual(c['entry_occurrence_counts']['aa'],2)
        self.assertEqual(c['base57']['owner_caps']['p'],20);self.assertEqual(c['price_caps']['p'][6],11)
        self.assertEqual(c['base57']['capped_prefixes']['p'][1],20);self.assertEqual(c['priced_prefixes']['p'][1],17)
        self.assertEqual(c['rows'][1]['charge_reduction_vs57'],3)
        dictionary=('a','b','X','aa')
        self.assertTrue(all(paths(text,dictionary) for text in texts.values()))
        self.assertEqual(sum(c['base57']['support'][w] is not None for w in dictionary),1)
        self.assertEqual(c['rows'][1]['integer_lower_bound'],-1) # gain is not a positive certificate

    def test_all_low_rank_arcs_and_zero_penalty_occurrences(self):
        texts={'p':'aaaa'};ban={'aaaa'}
        q={e:10 if len(w)==3 else 4 if len(w)==1 else 0 for e,w in p.parent.allowed(texts,ban).items()}
        c,_,_=self.check(texts,ban,q,[0,6,100],B=1)
        self.assertEqual(c['base57']['owner_top_entries']['p'],['aaa'])
        self.assertEqual(c['price_caps']['p'][0],16);self.assertEqual(c['price_caps']['p'][6],12)
        self.assertEqual(c['priced_prefixes']['p'],[0,16])
        self.assertEqual(c['entry_occurrence_counts']['aa'],3) # includes every zero-q occurrence
        self.assertEqual(c['price_caps']['p'][100],0)

    def test_floor_not_ceil_or_undercounted_multiplicity(self):
        texts={'p':'aa'};ban={'aa'};q={('p',0,1):1,('p',1,2):1}
        c,_,_=self.check(texts,ban,q,[0,1],B=1)
        self.assertEqual(c['entry_occurrence_counts']['a'],2);self.assertEqual(c['priced_prefixes']['p'],[0,2])
        wrong_residual=sum(max(v-1,0) for v in q.values()) # ceil(1/2) or wrong m=1
        self.assertGreater(sum(q.values()),1+wrong_residual)

    def test_lambda_zero_identity_no_owner_and_finite_zero_ties(self):
        texts={'p':'aba','s':'aca'};ban=set(texts.values());q={e:(e[1]+e[2])%4 for e in p.parent.allowed(texts,ban)}
        c,_,_=self.check(texts,ban,q,[0],B=4,D=3)
        self.assertEqual(c['priced_prefixes'],c['base57']['capped_prefixes'])
        self.assertTrue(all(row['charge_reduction_vs57']==0 for row in c['rows']))
        for B in (0,1,4):
            texts={'p':'ab','s':'ab'};ban={'ab'};q={e:0 for e in p.parent.allowed(texts,ban)}
            c,_,_=self.check(texts,ban,q,[0,2,9],B=B)
            self.assertEqual(c['entry_occurrence_counts'],{});self.assertEqual(c['one_owner_prefix'],[0])

    def test_random_tiny_all_paths_and_allocations(self):
        rng=random.Random(6301)
        for _ in range(16):
            texts={str(i):''.join(rng.choice('abc') for _ in range(3)) for i in range(2)};ban=set(texts.values())
            q={e:rng.randrange(9) for e in p.parent.allowed(texts,ban)}
            self.check(texts,ban,q,[0,1,3,8,21],B=3,D=3)

    def test_reject_missing_fake_negative_bool_and_optimization(self):
        texts={'p':'ab'};ban={'ab'};q={('p',0,1):1,('p',1,2):0}
        self.assertEqual(p.certificate(texts,iter(ban),q,[0],2),p.certificate(texts,ban,q,[0],2))
        for prices in ([],[1],[0,-1],[0,True],[0,0],[1,0],[0,1.0]):
            with self.assertRaises(AssertionError):p.certificate(texts,ban,q,prices)
        for bad in ({('p',0,1):1},{**q,('p',1,2):True},{**q,('p',1,2):-1},{**q,('p',0,2):0},{**q,('fake',0,1):0}):
            with self.assertRaises(AssertionError):p.certificate(texts,ban,bad,[0])
        for B,D in ((True,1),(1,True),(-1,1),(1,0)):
            with self.assertRaises(AssertionError):p.certificate(texts,ban,q,[0],B,D)
        proc=subprocess.run([sys.executable,'-O','-B','-c','import proof;proof.certificate({},set(),{},[0])'],cwd=Path(__file__).resolve().parent,capture_output=True,timeout=5)
        self.assertNotEqual(proc.returncode,0);self.assertIn(b'normal assertions required',proc.stderr)

if __name__=='__main__':unittest.main()
