"""Tiny exhaustive intervals, covering dictionaries and joint path choices."""
import itertools
import importlib.util
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
        for tail in schedules([arc for arc in ordered[index+1:] if arc[0]>=first[1]]):
            yield [first]+tail


class ProofTests(unittest.TestCase):
    def check(self,texts,banned,q,prices,B=3,D=1):
        result=p.certificate(texts,banned,q,prices,B,D)
        edges={(pid,i,j):text[i:j] for pid,text in texts.items()
               for i in range(len(text)) for j in range(i+1,len(text)+1) if text[i:j] not in banned}
        words=sorted(set(edges.values()))
        counts={word:sum(w==word for w in edges.values()) for word in words}
        self.assertEqual(result['entry_occurrence_counts'],counts)
        owners={word:{pid for (pid,i,j),w in edges.items() if w==word} for word in words}
        for pid,text in texts.items():
            intervals=[(i,j,w,q[pid,i,j]) for (source,i,j),w in edges.items() if source==pid]
            all_schedules=list(schedules(intervals))
            for index,price in enumerate(prices):
                residual=lambda word,value:max(value-price//counts[word],0)
                for end,value in enumerate(result['price_schedules'][pid][index]):
                    expected=max(sum(residual(w,v) for _,_,w,v in chosen)
                                 for chosen in all_schedules if all(j<=end for _,j,_,_ in chosen))
                    self.assertEqual(value,expected)
                self.assertEqual(result['price_caps'][pid][index],result['price_schedules'][pid][index][-1])
        for index,row in enumerate(result['price_rows']):
            self.assertEqual(row['charge'],prices[index]*B+sum(result['price_caps'][pid][index] for pid in texts))
            self.assertEqual(row['numerator'],result['base57']['L']-row['charge'])
            self.assertEqual(row['integer_lower_bound'],-(-row['numerator']//D))
        self.assertEqual(result['global']['charge'],min(row['charge'] for row in result['price_rows']))
        for row,old in zip(result['rows'],result['base57']['rows']):
            self.assertEqual(row['charge'],min(old['charge'],result['global']['charge']))
            self.assertEqual(row['integer_lower_bound'],-(-row['numerator']//D))
            self.assertGreaterEqual(row['integer_lower_bound'],old['integer_lower_bound'])
        full_L=0
        for pid,text in texts.items():
            values=[]
            for sequence in paths(text,words):
                pos=0;value=0
                for word in sequence:
                    end=pos+len(word);value+=D*(9 if len(word)==1 else -1)+q[pid,pos,end];pos=end
                values.append(value)
            full_L+=min(values)
        self.assertEqual(result['base57']['L'],full_L)
        dictionaries=joint_paths=0
        for size in range(min(B,len(words))+1):
            for dictionary in itertools.combinations(words,size):
                options=[paths(text,dictionary) for text in texts.values()]
                if not all(options):continue
                dictionaries+=1;k=sum(len(owners[word])==1 for word in dictionary)
                for selected in itertools.product(*options):
                    joint_paths+=1;Q=F=0;used=[]
                    for pid,sequence in zip(texts,selected):
                        pos=0
                        for word in sequence:
                            end=pos+len(word);value=q[pid,pos,end]
                            used.append((pid,pos,end,word,value));Q+=value;F+=9 if len(word)==1 else -1;pos=end
                    for index,price in enumerate(prices):
                        residual_total=0
                        for word in dictionary:
                            occurrence_values=[v for _,_,_,w,v in used if w==word]
                            removed=sum(min(v,price//counts[word]) for v in occurrence_values)
                            self.assertLessEqual(len(occurrence_values),counts[word])
                            self.assertLessEqual(removed,price)
                        for pid,text in texts.items():
                            residual=sum(max(v-price//counts[w],0) for source,_,_,w,v in used if source==pid)
                            self.assertLessEqual(residual,result['price_caps'][pid][index]);residual_total+=residual
                        self.assertLessEqual(Q-residual_total,price*len(dictionary))
                        self.assertLessEqual(Q,result['price_rows'][index]['charge'])
                    self.assertLessEqual(Q,result['global']['charge'])
                    self.assertLessEqual(Q,result['rows'][k]['charge'])
                    self.assertLessEqual(result['rows'][k]['numerator'],D*F)
                    self.assertLessEqual(result['rows'][k]['integer_lower_bound'],F)
        return result,dictionaries,joint_paths

    def test_positive_price_strict_over_zero_in_coverable_banned_whole_class(self):
        texts={'p':'abab'};banned={'abab'}
        q={edge:10 if edge in {('p',0,1),('p',1,3),('p',3,4)} else 0
           for edge in p.parent.allowed(texts,banned)}
        result,nd,np=self.check(texts,banned,q,[0,2],B=1,D=3)
        self.assertGreater(nd,0);self.assertGreater(np,0)
        self.assertEqual(paths('abab',['ab']),[('ab','ab')])
        self.assertEqual(result['entry_occurrence_counts']['a'],2)
        self.assertEqual([row['charge'] for row in result['price_rows']],[30,28])
        self.assertEqual(result['base57']['rows'][1]['charge'],10)
        self.assertEqual(result['rows'][1]['charge'],10) # positive-price gain is not gain over57
        self.assertLess(result['global']['numerator'],0)
        self.assertNotEqual(result['global']['numerator']%3,0)

    def test_zero_price_strict_over57_for_shared_overlapping_entries(self):
        texts={'p':'abc','s':'abc'};banned={'abc'}
        q={edge:10 if word in ('ab','bc') else 0 for edge,word in p.parent.allowed(texts,banned).items()}
        result,nd,np=self.check(texts,banned,q,[0,2,20],B=2,D=3)
        self.assertGreater(nd,0);self.assertGreater(np,0)
        self.assertEqual(result['entry_occurrence_counts']['ab'],2)
        self.assertEqual(result['base57']['rows'][0]['charge'],40)
        self.assertEqual(result['global']['charge'],20)
        self.assertEqual(result['rows'][0]['charge_reduction_vs57'],20)
        self.assertTrue(all(paths(text,['a','bc']) for text in texts.values()))
        self.assertEqual(result['rows'][0]['integer_lower_bound'],16)

    def test_positive_price_strict_over57_and60_with_whole_sources_banned(self):
        texts={'p':'aaabaaab','s':'aaabaaab'};banned={'aaabaaab'}
        q={edge:10 if word=='aa' else 5 if word=='b' else 0
           for edge,word in p.parent.allowed(texts,banned).items()}
        result,nd,np=self.check(texts,banned,q,[0,16],B=1)
        self.assertGreater(nd,0);self.assertGreater(np,0)
        self.assertEqual(result['entry_occurrence_counts']['aa'],8)
        self.assertEqual(result['entry_occurrence_counts']['b'],4)
        self.assertEqual([row['charge'] for row in result['price_rows']],[60,52])
        self.assertEqual(result['base57']['rows'][0]['charge'],80)
        self.assertEqual(result['rows'][0]['charge'],52)
        self.assertTrue(all(paths(text,['aaab'])==[('aaab','aaab')] for text in texts.values()))
        spec=importlib.util.spec_from_file_location('toy66_joint60',Path(__file__).resolve().parents[1]/'joint-path-cap-v1/proof.py')
        joint=importlib.util.module_from_spec(spec);spec.loader.exec_module(joint)
        baseline60=joint.certificate(texts,banned,q,1)
        self.assertEqual(baseline60['L'],result['base57']['L'])
        self.assertEqual(baseline60['rows'][0]['charge'],60)
        self.assertLess(result['global']['charge'],baseline60['rows'][0]['charge'])
        self.assertLess(result['rows'][0]['integer_lower_bound'],0) # strict but not a positive certificate

    def test_zero_price_does_not_recover57_and_global_bans(self):
        texts={'p':'ab','s':'ab'};banned=set()
        q={edge:int(len(word)==1) for edge,word in p.parent.allowed(texts,banned).items()}
        result,nd,np=self.check(texts,banned,q,[0],B=1)
        self.assertGreater(nd,0);self.assertGreater(np,0)
        self.assertEqual(result['global']['charge'],4);self.assertEqual(result['rows'][0]['charge'],2)
        banned={'a'};q={edge:0 for edge in p.parent.allowed(texts,banned)}
        result,nd,np=self.check(texts,banned,q,[0,3],B=1)
        self.assertGreater(nd,0);self.assertNotIn('a',result['entry_occurrence_counts'])
        self.assertEqual(result,p.certificate(texts,iter(banned),q,[0,3],1))

    def test_shared_count_includes_zero_and_overlapping_occurrences_floor_required(self):
        texts={'p':'aaa','s':'aaa'};banned={'aaa'}
        q={edge:int(edge[1]==0) for edge in p.parent.allowed(texts,banned)}
        result,_,_=self.check(texts,banned,q,[0,1,4,8],B=2)
        self.assertEqual(result['entry_occurrence_counts']['a'],6)
        self.assertEqual(result['entry_occurrence_counts']['aa'],4)
        texts={'p':'a','s':'a'};q={('p',0,1):1,('s',0,1):1}
        result,_,_=self.check(texts,set(),q,[0,1],B=1)
        self.assertEqual(result['global']['charge'],2)
        wrong=1+sum(max(value-1,0) for value in q.values()) # ceil(1/2), or wrong local m=1
        self.assertEqual(wrong,1);self.assertGreater(sum(q.values()),wrong)

    def test_random_complete_joint_paths_and_empty_capacity(self):
        rng=random.Random(6601)
        for _ in range(12):
            texts={str(i):''.join(rng.choice('abc') for _ in range(3)) for i in range(2)}
            banned=set(texts.values());q={edge:rng.randrange(8) for edge in p.parent.allowed(texts,banned)}
            self.check(texts,banned,q,[0,1,3,8,24],B=3,D=3)
        result,nd,np=self.check({'p':'ab'},{'ab'},{('p',0,1):0,('p',1,2):0},[0,2],B=0)
        self.assertEqual((nd,np),(0,0));self.assertEqual(result['global']['charge'],0)
        self.assertGreater(result['global']['integer_lower_bound'],0) # empty class, not a witness

    def test_reject_incomplete_fake_bool_negative_and_optimized_python(self):
        texts={'p':'ab'};banned={'ab'};q={('p',0,1):1,('p',1,2):0}
        for prices in ([],[1],[0,-1],[0,True],[0,0],[1,0],[0,1.0]):
            with self.assertRaises(AssertionError):p.certificate(texts,banned,q,prices)
        for bad in ({('p',0,1):1},{**q,('p',1,2):True},{**q,('p',1,2):-1},
                    {**q,('p',0,2):0},{**q,('fake',0,1):0},{('p',False,1):1,('p',1,2):0}):
            with self.assertRaises(AssertionError):p.certificate(texts,banned,bad,[0])
        for B,D in ((True,1),(-1,1),(1,True),(1,0)):
            with self.assertRaises(AssertionError):p.certificate(texts,banned,q,[0],B,D)
        with self.assertRaises(AssertionError):p.certificate(texts,{'a','ab'},q,[0])
        proc=subprocess.run([sys.executable,'-O','-B','-c','import proof;proof.certificate({},set(),{},[0])'],
                            cwd=Path(__file__).resolve().parent,capture_output=True,timeout=5)
        self.assertNotEqual(proc.returncode,0);self.assertIn(b'normal assertions required',proc.stderr)

if __name__=='__main__':unittest.main()
