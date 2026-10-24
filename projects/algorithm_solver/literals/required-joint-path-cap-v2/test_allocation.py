"""Pure allocation checks using tiny explicit graphs and exhaustive quotas."""
import copy
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest
import allocation as a
import proof


def supplied(certificate,B,D,L=None):
    base=certificate['base60']
    return dict(owner_prefixes=base['owner_prefixes'],
        capped_prefixes=certificate['base61']['base57']['capped_prefixes'],
        local_shared_prefixes=base['local_shared_prefixes'],all_caps=base['all_caps'],
        shared_prefix=base['shared_prefix'],forced_owners=certificate['forced_owners'],
        L=base['L'] if L is None else L,D=D,capacity=B)


class AllocationTests(unittest.TestCase):
    def both(self,kwargs):
        heap=a.heap(**kwargs);scan=a.scan(**kwargs)
        self.assertEqual({k:v for k,v in heap.items() if k!='work'},
                         {k:v for k,v in scan.items() if k!='work'})
        self.assertEqual(heap['work']['owner_scan_visits'],0)
        self.assertEqual(scan['work']['heap_offers'],0);self.assertEqual(scan['work']['heap_pops'],0)
        self.assertEqual(len(heap['rows']),kwargs['capacity']+1)
        return heap

    def compare(self,texts,banned,q,B=3,D=1):
        oracle=proof.certificate(texts,banned,q,B,D);got=self.both(supplied(oracle,B,D))
        self.assertEqual(got['owner61_prefix'],oracle['base61']['required_owner_prefix'])
        self.assertEqual(got['owner61_choices'],oracle['base61']['remaining_marginal_choices'])
        self.assertEqual(got['owner57_prefix'],dict(enumerate(oracle['base60']['prior57_one_owner_prefix'])))
        for rows,expected in ((got['rows'],oracle['rows']),(got['parent60_rows'],oracle['base60']['rows']),
                              (got['parent61_rows'],oracle['base61']['rows'])):
            for row,want in zip(rows,expected):
                for key in ('k','charge','one_owner_slots','numerator','integer_lower_bound'):
                    self.assertEqual(row[key],want[key],key)
        for split in oracle['split_rows']:
            actual=got['split_rows'][split['one_owner_slots']]
            for key,key2 in (('joint62_charge','joint_charge'),('charge61','prior61_charge'),('charge62','charge')):
                self.assertEqual(actual[key],split[key2])
            for key in ('zero_baseline','mandatory_baseline','mandatory_increment'):
                self.assertEqual(actual[key],split['allocation'][key])
            self.assertEqual(actual['required_choices'],split['allocation']['residual_choices'])
        return got

    def test_full_tiny_oracle_and_strict_both(self):
        texts={'p':'abc','q':'abd','u':'xyyx','v':'zz','w':'xx'};banned=set(texts.values())
        for D in (1,3):
            q={e:0 if e[2]-e[1]==1 else (9*(e[2]-e[1])+1)*D for e in proof.joint.allowed(texts,banned)}
            got=self.compare(texts,banned,q,6,D)
            self.assertEqual(got['rows'][4]['charge'],66*D)
            self.assertEqual(got['rows'][4]['integer_lower_bound'],60)
            self.assertEqual(got['rows'][4]['integer_gain_vs60'],10)
            self.assertEqual(got['rows'][4]['integer_gain_vs61'],38)

    def test_random_complete_prefix_and_parent_curve_reconstruction(self):
        rng=random.Random(6201)
        for _ in range(24):
            texts={str(i):''.join(rng.choice('abc') for _ in range(3)) for i in range(2)}
            banned=set(texts.values());q={e:rng.randrange(15) for e in proof.joint.allowed(texts,banned)}
            for B in (0,1,3,8):self.compare(texts,banned,q,B,3)
        texts={'p':'aba','q':'abc'};banned=set(texts.values())
        self.compare(texts,banned,{e:3 for e in proof.joint.allowed(texts,banned)},256,2)

    def test_mandatory_saturation_exhaustive_allocation(self):
        kwargs=dict(owner_prefixes={'a':[0,4,8],'b':[0,5,7]},capped_prefixes={'a':[0,4,6],'b':[0,5,7]},
            local_shared_prefixes={'a':[0,7],'b':[0,3]},all_caps={'a':7,'b':10},shared_prefix=[0,10],
            forced_owners=['a'],L=-11,D=3,capacity=2)
        got=self.both(kwargs)
        self.assertEqual(got['split_rows'][1]['zero_baseline'],10)
        self.assertEqual(got['split_rows'][1]['mandatory_baseline'],10)
        self.assertEqual(got['split_rows'][1]['mandatory_increment'],0)
        for split in got['split_rows']:
            j=split['one_owner_slots'];s=2-j
            if j<1:continue
            vectors=[ts for ts in itertools.product(range(1,3),range(3)) if sum(ts)==j]
            def joint(ts):
                return sum(min(kwargs['local_shared_prefixes'][pid][min(s,1)]+kwargs['owner_prefixes'][pid][t],kwargs['all_caps'][pid])
                           for pid,t in zip(('a','b'),ts))
            self.assertEqual(split['joint62_charge'],max(map(joint,vectors)))
        for row in got['rows'][1:]:
            self.assertLess(row['numerator'],0);self.assertEqual(row['integer_lower_bound'],-(-row['numerator']//3))

    def test_finite_zeros_ties_clipping_and_capacity_floor(self):
        kwargs=dict(owner_prefixes={'a':[0,0,0],'b':[0,0]},capped_prefixes={'a':[0,0,0],'b':[0,0]},
            local_shared_prefixes={'a':[0,0],'b':[0,0]},all_caps={'a':0,'b':0},shared_prefix=[0,0],
            forced_owners=['b'],L=0,D=1,capacity=5)
        got=self.both(kwargs)
        self.assertEqual(len(got['split_rows']),4)
        self.assertEqual(got['owner61_choices'],[('a',1,0),('a',2,0)])
        self.assertTrue(all(row['one_owner_slots']==1 for row in got['rows'][1:]))
        self.assertEqual(got['split_rows'][1]['shared_slots_available'],1)
        kwargs=dict(owner_prefixes={'a':[0],'b':[0]},capped_prefixes={'a':[0],'b':[0]},
            local_shared_prefixes={'a':[0],'b':[0]},all_caps={'a':0,'b':0},shared_prefix=[0],
            forced_owners=['a','b'],L=0,D=1,capacity=0)
        self.assertTrue(self.both(kwargs)['rows'][0]['empty_by_required_owners'])
        kwargs.update(owner_prefixes={'a':[0,1],'b':[0,2]},capped_prefixes={'a':[0,1],'b':[0,2]},
            all_caps={'a':1,'b':2},capacity=1)
        self.assertTrue(all(row['charge'] is None for row in self.both(kwargs)['rows']))

    def test_shape_provenance_boundaries_and_invalid_numbers(self):
        valid=dict(owner_prefixes={'a':[0,4,8]},capped_prefixes={'a':[0,4,6]},
            local_shared_prefixes={'a':[0,3]},all_caps={'a':7},shared_prefix=[0,5],
            forced_owners=['a'],L=4,D=2,capacity=2)
        self.both(valid)
        bad_updates=[{'L':True},{'D':False},{'D':0},{'D':float('inf')},{'capacity':True},{'capacity':257},
            {'all_caps':{'a':6.0}},{'all_caps':{'a':5}},{'all_caps':{'a':float('nan')}},
            {'owner_prefixes':{'a':[0,4,9]}},{'owner_prefixes':{'a':[0,True,2]}},
            {'capped_prefixes':{'a':[0,3,6]}},{'capped_prefixes':{'a':[0,4]}},
            {'local_shared_prefixes':{'a':[0,6]}},{'local_shared_prefixes':{'a':[0]}},
            {'local_shared_prefixes':{'a':[0,1,3]}},{'shared_prefix':[0,5.0]},
            {'forced_owners':['missing']},{'forced_owners':['a','a']},{'forced_owners':[True]},
            {'all_caps':{}},{'owner_prefixes':{}},{'capped_prefixes':{'a':[0,4,6],'x':[0]}},
            {'owner_prefixes':{'a':[0]},'capped_prefixes':{'a':[0]}}]
        for update in bad_updates:
            for method in (a.heap,a.scan):
                with self.subTest(update=update,method=method.__name__),self.assertRaises(AssertionError):method(**(valid|update))
        # The API validates numerical consistency; changing an otherwise valid
        # shared identity/provenance cannot be detected because none is supplied.
        result=self.both(valid|{'forced_owners':[]})
        self.assertEqual(result['coverage_floor'],0)

    def test_real_multidigit_json_roundtrip(self):
        kwargs=dict(owner_prefixes={str(i):list(range(13)) for i in range(3)},
            capped_prefixes={str(i):list(range(13)) for i in range(3)},
            local_shared_prefixes={str(i):[0] for i in range(3)},
            all_caps={str(i):12 for i in range(3)},shared_prefix=[0],
            forced_owners=['0','1','2'],L=50,D=3,capacity=256)
        outputs=[]
        for method in (a.heap,a.scan):
            original=method(**kwargs);loaded=json.loads(json.dumps(original))
            self.assertIn('12',loaded['owner57_prefix']);self.assertIn('12',loaded['owner61_prefix'])
            for field,h in loaded['digests'].items():
                key=field.removesuffix('_sha256')
                self.assertEqual(a.digest(original[key]),h)
                self.assertEqual(a.digest(loaded[key]),h)
            for key in ('owner57_prefix','owner61_prefix'):
                bad=copy.deepcopy(loaded[key]);bad['12']+=1
                self.assertNotEqual(a.digest(bad),loaded['digests'][key+'_sha256'])
                bad=copy.deepcopy(loaded[key]);bad['012']=bad.pop('12')
                self.assertNotEqual(a.digest(bad),loaded['digests'][key+'_sha256'])
            outputs.append({k:v for k,v in loaded.items() if k!='work'})
        self.assertEqual(*outputs)

    def test_no_mutation_and_optimized_python(self):
        text={'p':'abc','q':'abd'};banned=set(text.values());q={e:3 for e in proof.joint.allowed(text,banned)}
        kwargs=supplied(proof.certificate(text,banned,q,3),3,1);before=copy.deepcopy(kwargs)
        self.both(kwargs);self.assertEqual(kwargs,before)
        script="import allocation;allocation.heap({}, {}, {}, {}, [0], [], 0, 1)"
        proc=subprocess.run([sys.executable,'-O','-B','-c',script],cwd=Path(__file__).resolve().parent,
            capture_output=True,text=True,timeout=5)
        self.assertNotEqual(proc.returncode,0);self.assertIn('normal assertions required',proc.stderr)


if __name__=='__main__':unittest.main()
