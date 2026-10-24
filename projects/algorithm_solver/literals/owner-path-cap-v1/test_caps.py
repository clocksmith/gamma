"""Paired supplied-input kernels and explicit forward-schedule checks."""
import random
import subprocess
import sys
from pathlib import Path
import unittest
import caps
import independent
import proof
from test_independent import fixture,explicit

BASE=('lifted','tightened','new_only_class_counts','new_only_top_entries','digests','reductions','deltas')
COMMON=('owner_caps','owner_top_entries','owner_entry_counts','owner_prefixes','capped_prefixes',
        'one_owner_prefix','marginal_choices','shared_prefix','rows','deltas_vs53')


class CapsTests(unittest.TestCase):
    def compare(self,kw,B):
        got=caps.check(**kw,capacity=B);other=independent.check(**kw,capacity=B)
        for key in BASE:self.assertEqual(got['base'][key],other['base'][key],key)
        for key in COMMON:self.assertEqual(got[key],other[key],key)
        q,_=explicit(kw);oracle=proof.certificate(kw['texts'],kw['banned'],q,B,kw['D'])
        self.assertEqual(got['owner_prefix_schedule'],oracle['owner_schedule_values'])
        for key in got['digests'].keys()&other['digests'].keys():self.assertEqual(got['digests'][key],other['digests'][key],key)
        self.assertEqual(got['work']['schedule_endpoints_inspected'],other['work']['schedule_endpoints_inspected'])
        self.assertEqual(got['work']['schedule_one_owner_occurrences'],other['work']['schedule_occurrences_admitted'])
        return got

    def test_many_tiny_sources_and_capacities(self):
        rng=random.Random(5704)
        for _ in range(16):
            texts={str(i):''.join(rng.choice('abcd') for _ in range(5)) for i in range(3)}
            kw=fixture(texts,set(texts.values()),rng=rng)
            for B in (0,1,3,8):self.compare(kw,B)

    def test_repeated_old_seed_and_full_schedule(self):
        kw=fixture({'p':'aaaa'},{'aaaa'},seed=['aaa','~~'],D=1)
        kw['old_q']=[4,10,4,10,4,4]
        got=self.compare(kw,1)
        self.assertEqual(got['owner_top_entries']['p'][0][0],27)
        self.assertEqual(got['owner_caps']['p'],31)
        self.compare(kw,256)

    def test_banned_shared_depths_and_distinct_owner_storage(self):
        self.compare(fixture({'10':'abcxabc','2':'abcyabc'},{'abc','abcxabc','abcyabc'},seed=['cx','~~']),7)
        got=self.compare(fixture({'10':'abcd','2':'efgh','3':'ijkl'}),2)
        self.assertEqual(sum(map(len,got['owner_top_entries'].values())),6)
        self.assertEqual(got['work']['owner_unique_entries_extracted'],6)

    def test_zero_ties_and_guard(self):
        kw=fixture({'b':'xx','a':'yy'},{'xx','yy'});kw['old_q']=[0]*len(kw['old_q'])
        self.compare(kw,8)
        script='import caps;caps.check({},set(),[],[],[],[],1,expected_source_hashes={},expected_old_banned=set())'
        proc=subprocess.run([sys.executable,'-O','-B','-c',script],cwd=Path(__file__).resolve().parent,capture_output=True,timeout=5)
        self.assertNotEqual(proc.returncode,0);self.assertIn(b'normal assertions required',proc.stderr)


if __name__=='__main__':unittest.main()
