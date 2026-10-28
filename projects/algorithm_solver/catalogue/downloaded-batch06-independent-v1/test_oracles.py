import copy,math,unittest
from itertools import combinations,product
import oracles as o

class HostReferenceChecks(unittest.TestCase):
    def test_case_generation_is_hash_seed_independent(self):
        import os,subprocess,sys
        code="import cases,json,hashlib;print(hashlib.sha256(json.dumps(cases.build(),sort_keys=True,separators=(',',':')).encode()).hexdigest())"
        digests=[]
        for seed in ('11','29'):
            env=dict(os.environ,PYTHONHASHSEED=seed,PYTHONDONTWRITEBYTECODE='1')
            digests.append(subprocess.check_output([sys.executable,'-c',code],cwd=__import__('pathlib').Path(__file__).resolve().parent,env=env))
        self.assertEqual(*digests)
    def test_monotone_enumeration_against_scan(self):
        best=0
        for n in range(2001):
            if list(str(n))==sorted(str(n)):best=n
            self.assertEqual(o.expected(738,[n]),best)
        self.assertEqual(o.expected(738,[10**9]),999999999)
    def test_tiling_transfer_against_independent_exact_cover(self):
        for n in range(1,7):
            cells=set(product(range(2),range(n)));tiles=set()
            for r,c in cells:
                for dr,dc in ((1,0),(0,1)):
                    tile=frozenset(((r,c),(r+dr,c+dc)))
                    if tile<=cells:tiles.add(tile)
                square={(r,c),(r+1,c),(r,c+1),(r+1,c+1)}
                for missing in square:
                    tile=frozenset(square-{missing})
                    if tile<=cells:tiles.add(tile)
            def covers(left):
                if not left:return 1
                first=min(left)
                return sum(covers(left-set(t))for t in tiles if first in t and t<=left)
            self.assertEqual(o.tilings(n),covers(cells))
    def test_odd_divisor_theorem_against_positive_runs(self):
        for n in range(1,151):
            count=0
            for start in range(1,n+1):
                total=0
                for value in range(start,n+1):
                    total+=value
                    if total>=n:
                        count+=total==n;break
            self.assertEqual(o.expected(829,[n]),count)
    def test_game_tree_against_xor_characterization(self):
        for n in range(1,6):
            for xs in product(range(3),repeat=n):
                xor=0
                for v in xs:xor^=v
                self.assertEqual(o.expected(810,[list(xs)]),xor==0 or n%2==0)
    def test_terminal_game_and_puzzle_controls(self):
        self.assertTrue(o.expected(794,[['   ','   ','   ']]))
        self.assertFalse(o.expected(794,[['XXX','OOO','   ']]))
        self.assertFalse(o.expected(794,[['XXX','OO ',' O ']]))
        self.assertEqual(len(o.puzzle_distances()),360)
        self.assertEqual(o.expected(773,[[[1,2,3],[5,4,0]]]),-1)
    def test_freedom_and_observation_rejections(self):
        self.assertTrue(o.matches(760,[[1,1],[1,1]],[1,0],None))
        self.assertFalse(o.matches(760,[[1,1],[1,1]],[True,0],None))
        self.assertTrue(o.matches(791,['cba','abcd'],'dcba',None))
        self.assertFalse(o.matches(791,['cba','abcd'],'abcd',None))
        self.assertTrue(o.matches(797,[],[[0,2],[0,1,2]],[[0,1,2],[0,2]]))
        args=[[1,2]];record={'result':[],'result_type':'list','args_before':args,'args_after':args,'alias_edges':[]}
        self.assertTrue(o.compare(735,args,[],record,'python')[0])
        changed=copy.deepcopy(record);changed['alias_edges']=[['result','args.0']]
        self.assertEqual(o.compare(735,args,[],changed,'python'),(False,'mutable_alias'))
        changed=copy.deepcopy(record);changed['args_after']=[[2,1]]
        self.assertEqual(o.compare(735,args,[],changed,'python'),(False,'input_effects'))
if __name__=='__main__':unittest.main()
