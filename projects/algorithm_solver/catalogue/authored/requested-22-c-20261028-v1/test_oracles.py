import importlib.util
from pathlib import Path
import random
import unittest
_spec=importlib.util.spec_from_file_location('gamma_r22c_reference_test_oracles',Path(__file__).with_name('oracles.py'))
_o=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_o)
reference,validate_domain,compare=_o.reference,_o.validate_domain,_o.compare
NAMES=['a','b','c','xy','zz','ab']
def random_expression(rng,depth):
    if depth==0 or rng.random()<0.3:
        return rng.choice(NAMES) if rng.random()<0.6 else str(rng.randrange(0,12))
    left,right=random_expression(rng,depth-1),random_expression(rng,depth-1)
    text=left+' '+rng.choice('+-*')+' '+right
    return '('+text+')' if rng.random()<0.5 else text
class References(unittest.TestCase):
    def test_polynomial_format(self):
        self.assertEqual(reference(770,['b * a + 3 * a * a - 2',[],[]]),['3*a*a','1*a*b','-2'])
        self.assertEqual(reference(770,['x - x',[],[]]),[])
        self.assertEqual(reference(770,['(p + 1) * q',['q'],[-3]]),['-3*p','-3'])
    def test_polynomial_matches_python_evaluation(self):
        rng=random.Random(770)
        for _ in range(300):
            text=random_expression(rng,4)
            if text.startswith('(') and text.endswith(')') and len(text)>250:continue
            fixed=rng.sample(NAMES,rng.randrange(0,3));ints=[rng.randrange(-5,6) for _ in fixed]
            try:terms=reference(770,[text,fixed,ints])
            except ValueError:continue
            env={name:rng.randrange(-7,8) for name in NAMES};env.update(zip(fixed,ints))
            value=0
            for term in terms:
                parts=term.split('*');product=int(parts[0])
                self.assertNotEqual(product,0);self.assertEqual(parts[1:],sorted(parts[1:]))
                for name in parts[1:]:
                    self.assertNotIn(name,fixed);product*=env[name]
                value+=product
            self.assertEqual(value,eval(text,{'__builtins__':{}},dict(env)))
            keys=[(-len(t.split('*'))+1,t.split('*')[1:]) for t in terms];self.assertEqual(keys,sorted(keys));self.assertEqual(len({tuple(k[1]) for k in keys}),len(keys))
    def test_expression_domain(self):
        for bad in [' a','a  + b','a +','(a + b','2x','a + -b','a)']:
            with self.assertRaises(ValueError):validate_domain(770,[bad,[],[]])
    def test_chessboard(self):
        self.assertEqual(reference(782,[[[1,0],[0,1]]]),0);self.assertEqual(reference(782,[[[0,0],[1,1]]]),-1)
        self.assertEqual(reference(782,[[[1,0,1],[1,0,1],[0,1,0]]]),1)
    def test_champagne(self):
        self.assertEqual(reference(799,[5,2,0]),0.5);self.assertEqual(reference(799,[5,2,1]),1.0);self.assertEqual(reference(799,[0,0,0]),0.0)
    def test_bricks(self):
        self.assertEqual(reference(803,[[[1,1],[0,1]],[[0,1],[0,0]]]),[1,0])
        self.assertEqual(reference(803,[[[0,1],[1,1]],[[1,0],[0,1]]]),[0,1])
        self.assertEqual(reference(803,[[[1,0],[0,1]],[[1,1],[0,0]]]),[0,0])
    def test_average_split_paths_agree(self):
        rng=random.Random(805)
        self.assertFalse(reference(805,[[7]]));self.assertTrue(reference(805,[[2,2]]));self.assertFalse(reference(805,[[1,3]]))
        for _ in range(200):
            nums=[rng.randrange(0,20) for _ in range(rng.randrange(1,13))]
            n=len(nums);total=sum(nums);reach=[0]*(n+1);reach[0]=1
            for x in nums:
                for k in range(n,0,-1):reach[k]|=reach[k-1]<<x
            self.assertEqual(reference(805,[nums]),any(total*k%n==0 and reach[k]>>(total*k//n)&1 for k in range(1,n)))
    def test_soup_decimal_matches_exact_millilitres(self):
        for n in [0,1,24,25,26,49,50,51,99,100,130,240,499,1000,1500]:
            self.assertAlmostEqual(reference(808,[n]),float(_o.soup_exact_ml(n)),places=12)
    def test_soup_certificate(self):
        self.assertLess(_o.soup_hoeffding_tail(_o.SOUP_TABLE_UNITS+1),1e-6);self.assertEqual(reference(808,[10**9]),1.0)
    def test_components(self):
        self.assertEqual(reference(817,[{'values':[2,0,1]},[2,1]]),2);self.assertEqual(reference(817,[{'values':[0]},[0]]),1)
        with self.assertRaises(ValueError):validate_domain(817,[{'values':[0,0]},[0]])
    def test_race(self):
        self.assertEqual(reference(818,[1]),1);self.assertEqual(reference(818,[2]),4);self.assertEqual(reference(818,[7]),3);self.assertEqual(reference(818,[8191]),13)
    def test_tolerance_comparator(self):
        self.assertTrue(compare(799,0.500009,0.5));self.assertFalse(compare(799,0.50002,0.5));self.assertFalse(compare(808,True,1.0));self.assertFalse(compare(817,2.0,2))
if __name__=='__main__':unittest.main()
