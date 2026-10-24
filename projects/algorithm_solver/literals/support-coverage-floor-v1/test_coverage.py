"""Invented exhaustive coverage-floor and distinct-owner checks."""
import itertools
import random
import subprocess
import sys
from pathlib import Path
import unittest
import coverage as c


def universe(texts,banned):
    return sorted({t[i:j] for t in texts.values() for i in range(len(t)) for j in range(i+1,len(t)+1)}-set(banned))


def covers(text,vocab):
    good={0}
    for i in range(len(text)):
        if i in good:
            for word in vocab:
                if text.startswith(word,i):good.add(i+len(word))
    return len(text) in good


class CoverageTests(unittest.TestCase):
    def test_optimized_python_rejects_both_entry_points(self):
        for entry in ('production','replay'):
            proc=subprocess.run([sys.executable,'-O','-c',
                f'import coverage; coverage.{entry}({{"1":"ab"}},["a","b"],{{"ab"}})'],
                cwd=Path(__file__).resolve().parent,capture_output=True,text=True,timeout=5)
            self.assertNotEqual(proc.returncode,0)
            self.assertIn('RuntimeError: normal assertions required',proc.stderr)

    def check(self,texts,banned):
        full=universe(texts,banned)
        pool=sorted({w for w in full if len(w)==1 or sum(w in t for t in texts.values())>=2}|{'z'})
        a=c.production(texts,pool,banned);b=c.replay(texts,pool,banned)
        self.assertEqual({k:v for k,v in a.items() if k!='prefix_reachable'},
                         {k:v for k,v in b.items() if k!='suffix_reachable'})
        shared=[w for w in full if sum(w in t for t in texts.values())>=2]
        self.assertEqual([pool[i] for i in a['shared_entry_ids']],shared)
        self.assertEqual(a['source_success'],{p:covers(t,shared) for p,t in texts.items()})
        floor=len(a['forced_source_ids'])
        for size in range(len(full)+1):
            for vocab in itertools.combinations(full,size):
                if all(covers(t,vocab) for t in texts.values()):
                    self.assertGreaterEqual(sum(sum(w in t for t in texts.values())==1 for w in vocab),floor)
        return a
    def test_three_required_owners_and_feasible_floor(self):
        a=self.check({'1':'ab','2':'ac','3':'ad'},{'ab','ac','ad'})
        self.assertEqual(len(a['forced_source_ids']),3)
    def test_repeated_occurrences_are_not_extra_owners(self):
        a=self.check({'1':'aa','2':'bb'},{'aa','bb'})
        self.assertEqual(a['owner_classes'],[1,1,0]);self.assertEqual(a['occurrences'],4)
    def test_shared_banned_singleton_can_force_more_than_character_floor(self):
        a=self.check({'1':'abc','2':'bac'},{'a','abc','bac'})
        self.assertEqual(len(a['forced_source_ids']),2);self.assertEqual(a['private_character_entries'],0)
    def test_zero_floor_is_not_capacity_feasibility(self):
        a=self.check({'1':'ab','2':'ba'},{'ab','ba'})
        self.assertEqual(a['forced_source_ids'],[])
        self.assertFalse(any(all(covers(t,[w]) for t in ('ab','ba')) for w in ('a','b')))
    def test_small_random_exhaustive(self):
        rng=random.Random(56)
        for _ in range(12):
            texts={str(i):''.join(rng.choice('ab') for _ in range(3)) for i in range(2)}
            self.check(texts,set(texts.values()))

if __name__=='__main__':unittest.main()
