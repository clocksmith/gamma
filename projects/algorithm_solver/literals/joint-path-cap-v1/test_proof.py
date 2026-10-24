"""Independent exhaustive invented dictionary/path, interval and quota oracles."""
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


def schedule(intervals):
    best=0
    for size in range(len(intervals)+1):
        for group in itertools.combinations(intervals,size):
            chosen=sorted(group)
            if all(a[1]<=b[0] for a,b in zip(chosen,chosen[1:])):best=max(best,sum(v for _,_,v in chosen))
    return best


class ProofTests(unittest.TestCase):
    def check(self,texts,banned,q,B=3,D=1):
        got=p.certificate(texts,banned,q,B,D)
        words=sorted({text[i:j] for text in texts.values() for i in range(len(text)) for j in range(i+1,len(text)+1) if text[i:j] not in banned})
        owners={w:{pid for pid,text in texts.items() if w in text} for w in words}
        local={pid:{w:sum(q[pid,i,j] for i in range(len(text)) for j in range(i+1,len(text)+1) if text[i:j]==w) for w in words} for pid,text in texts.items()}
        weights={w:sum(local[pid][w] for pid in texts) for w in words}
        shared=[w for w in words if len(owners[w])>1];owner_words={pid:[w for w in words if owners[w]=={pid}] for pid in texts}
        caps={};onecaps={};L=0
        for pid,text in texts.items():
            arcs=[(i,j,q[pid,i,j]) for i in range(len(text)) for j in range(i+1,len(text)+1) if text[i:j] in owners]
            caps[pid]=schedule(arcs);onecaps[pid]=schedule([(i,j,v) for i,j,v in arcs if owners[text[i:j]]=={pid}])
            self.assertEqual(got['all_caps'][pid],caps[pid]);self.assertEqual(got['one_owner_caps'][pid],onecaps[pid])
            costs=[]
            for sequence in paths(text,words):
                at=0;value=0
                for w in sequence:value+=D*(9 if len(w)==1 else -1)+q[pid,at,at+len(w)];at+=len(w)
                costs.append(value)
            L+=min(costs)
        self.assertEqual(got['L'],L);self.assertEqual(got['weights'],weights)
        owners_order=sorted(texts);alternatives=[]
        for j in range(min(B,sum(map(len,owner_words.values())))+1):
            s=B-j;oldbest=jointbest=-1
            Sp={pid:sum(sorted((local[pid][w] for w in shared),reverse=True)[:s]) for pid in owners_order}
            A={pid:[0]+[sum(sorted((weights[w] for w in owner_words[pid]),reverse=True)[:t]) for t in range(1,min(B,len(owner_words[pid]))+1)] for pid in owners_order}
            for allocation in itertools.product(*(range(len(A[pid])) for pid in owners_order)):
                if sum(allocation)>j:continue
                jointbest=max(jointbest,sum(min(Sp[pid]+A[pid][t],caps[pid]) for pid,t in zip(owners_order,allocation)))
                oldbest=max(oldbest,sum(min(A[pid][t],onecaps[pid]) for pid,t in zip(owners_order,allocation)))
            prior=oldbest+sum(sorted((weights[w] for w in shared),reverse=True)[:s])
            actual=got['alternatives'][j]
            self.assertEqual(actual['joint_charge'],jointbest);self.assertEqual(actual['prior57_charge'],prior)
            self.assertEqual(actual['charge'],min(jointbest,prior));alternatives.append((min(jointbest,prior),prior))
            fs=actual['owner_functions'];marginals=[]
            for pid,values in fs.items():
                diffs=[b-a for a,b in zip(values,values[1:])]
                self.assertEqual(diffs,sorted(diffs,reverse=True));self.assertTrue(all(x>=0 for x in diffs))
                marginals += [(v,pid,t) for t,v in enumerate(diffs,1)]
            ordered=sorted(marginals,key=lambda x:(-x[0],x[1],x[2]))[:j]
            self.assertEqual(actual['allocation_choices'],[(pid,t,v) for v,pid,t in ordered])
            self.assertEqual(jointbest,sum(v[0] for v in fs.values())+sum(v for v,_,_ in ordered))
        prior_charge=-1
        for row in got['rows']:
            choices=alternatives[:min(row['k'],len(alternatives)-1)+1]
            self.assertEqual(row['charge'],max(a for a,b in choices));self.assertEqual(row['prior57_charge'],max(b for a,b in choices))
            self.assertLessEqual(row['charge'],row['prior57_charge']);self.assertGreaterEqual(row['charge'],prior_charge);prior_charge=row['charge']
            self.assertEqual(row['integer_lower_bound'],-(-row['numerator']//D))
        covering=path_count=0
        for size in range(min(B,len(words))+1):
            for dictionary in itertools.combinations(words,size):
                allpaths=[paths(text,dictionary) for text in texts.values()]
                if not all(allpaths):continue
                covering+=1;j=sum(len(owners[w])==1 for w in dictionary)
                for choice in itertools.product(*allpaths):
                    path_count+=1;F=Q=0;localQ={}
                    for pid,sequence in zip(texts,choice):
                        at=0;localQ[pid]=0
                        for w in sequence:
                            value=q[pid,at,at+len(w)];Q+=value;localQ[pid]+=value;F+=9 if len(w)==1 else -1;at+=len(w)
                        jp=sum(owners[w]=={pid} for w in dictionary)
                        Sp=sum(sorted((local[pid][w] for w in shared),reverse=True)[:B-j])
                        Ap=sum(sorted((weights[w] for w in owner_words[pid]),reverse=True)[:jp])
                        self.assertLessEqual(localQ[pid],min(Sp+Ap,caps[pid]))
                    for row in got['rows'][j:]:
                        self.assertLessEqual(Q,row['charge']);self.assertLessEqual(L-row['charge'],D*F)
                        self.assertLessEqual(row['integer_lower_bound'],F)
        return got,covering,path_count

    def test_strict_joint_gain_at_fixed53_q_with_covering_dictionary(self):
        texts={'p':'abc','q':'abd'};banned=set(texts.values())
        for D in (1,3):
            d={pid:[9*D*(len(t)-i) for i in range(len(t)+1)] for pid,t in texts.items()}
            q={edge:max(0,d[edge[0]][edge[1]]-d[edge[0]][edge[2]]-D*(9 if edge[2]-edge[1]==1 else -1)) for edge in p.allowed(texts,banned)}
            got,nd,np=self.check(texts,banned,q,3,D)
            self.assertEqual(got['distances'],d);self.assertGreater(nd,0);self.assertGreater(np,0)
            self.assertEqual(got['rows'][2]['prior57_charge'],76*D);self.assertEqual(got['rows'][2]['charge'],38*D)
            self.assertEqual(got['rows'][2]['integer_lower_bound'],16)
            self.assertEqual(paths('abc',{'a','bc','bd'}),[('a','bc')]);self.assertEqual(paths('abd',{'a','bc','bd'}),[('a','bd')])
    def test_shared_coupling_is_relaxed_and_min_with57_is_needed(self):
        texts={'p':'ab','q':'ab'};banned={'ab'}
        q={('p',0,1):10,('p',1,2):0,('q',0,1):0,('q',1,2):10}
        got,_,_=self.check(texts,banned,q,B=1)
        self.assertEqual(got['alternatives'][0]['joint_charge'],20)
        self.assertEqual(got['alternatives'][0]['prior57_charge'],10)
        self.assertEqual(got['rows'][0]['charge'],10)
        self.assertNotEqual(got['local_shared_top_entries']['p'],got['local_shared_top_entries']['q'])
    def test_repeated_occurrences_all_arcs_and_shared_singletons(self):
        texts={'p':'aaaa','q':'aaab'};banned=set(texts.values())
        q={edge:(7 if edge[2]-edge[1]==3 else 2) for edge in p.allowed(texts,banned)}
        got,nd,np=self.check(texts,banned,q,B=3,D=2)
        self.assertIsNone(got['support']['a']);self.assertEqual(got['support']['b'],'q')
        self.assertGreater(got['weights']['aaa'],7);self.assertGreater(nd,0);self.assertGreater(np,0)
    def test_baseline_zero_caps_ties_and_finite_entry_counts(self):
        for B in (0,1,2,5):
            texts={'p':'a','q':'b'};q={('p',0,1):0,('q',0,1):0}
            got,_,_=self.check(texts,set(),q,B)
            self.assertEqual(len(got['alternatives']),min(B,2)+1)
            self.assertTrue(all(row['one_owner_slots']==0 for row in got['rows']))
        totals,choices=p.allocate({'b':[5,5,5],'a':[7,7,7]},3)
        self.assertEqual(totals,[12,12,12,12]);self.assertEqual(choices,[('a',1,0),('a',2,0),('b',1,0)])
    def test_deterministic_random_exhaustive(self):
        rng=random.Random(60)
        for _ in range(18):
            texts={str(i):''.join(rng.choice('abc') for _ in range(3)) for i in range(2)};banned=set(texts.values())
            q={edge:rng.randrange(8) for edge in p.allowed(texts,banned)}
            self.check(texts,banned,q,B=3,D=3)
    def test_invalid_missing_penalties_uncovered_graph_and_optimized_python(self):
        texts={'p':'ab'};banned={'ab'};q={('p',0,1):1,('p',1,2):0}
        for bad in ({('p',0,1):1},{**q,('p',1,2):-1},{**q,('p',1,2):True}):
            with self.assertRaises(AssertionError):p.certificate(texts,banned,bad,3)
        with self.assertRaises(AssertionError):p.certificate({'p':'a'},{'a'},{},3)
        proc=subprocess.run([sys.executable,'-O','-c','import proof;proof.certificate({},set(),{})'],cwd=Path(__file__).resolve().parent,capture_output=True,text=True,timeout=5)
        self.assertNotEqual(proc.returncode,0);self.assertIn('normal assertions required',proc.stderr)
if __name__=='__main__':unittest.main()
