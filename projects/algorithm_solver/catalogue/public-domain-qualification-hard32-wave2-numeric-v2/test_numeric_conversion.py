"""Independent exact-Fraction boundary controls; no candidate execution."""
from decimal import Decimal,localcontext
from fractions import Fraction
import math,unittest
from oracle import compare
class NumericConversion(unittest.TestCase):
 def record(self,value,kind='float'):
  return {'result':value,'result_type':kind,'args_before':[[[0,0],[3,4]]],'args_after':[[[0,0],[3,4]]],'alias_edges':[]}
 def want(self,text):return {'analytic_decimal':text,'oracle_absolute_uncertainty':'1e-35','official_absolute_tolerance':'1e-5'}
 def test_nextafter_both_absolute_boundaries_against_exact_fraction(self):
  limit=Fraction(1,100000)-Fraction(1,10**35)
  for center in(0.,5.,7000.):
   for sign in(-1,1):
    edge=center+sign*1e-5
    for value in(math.nextafter(edge,-math.inf),edge,math.nextafter(edge,math.inf)):
     exact=abs(Fraction.from_float(value)-Fraction.from_float(center))<=limit
     self.assertEqual(compare(1515,[[[0,0],[3,4]]],self.want(str(center)),self.record(value),'python')[0],exact)
 def test_decimal_str_rounding_false_accept_counterexample(self):
  with localcontext()as c:
   c.prec=1200
   center=Decimal('0.1')-Decimal('1e-5')+Decimal('2e-35')
   old_difference=abs(Decimal(str(0.1))-center)
   self.assertLessEqual(old_difference,Decimal('1e-5')-Decimal('1e-35'))
   self.assertGreater(abs(Decimal.from_float(0.1)-center),Decimal('1e-5'))
   self.assertFalse(compare(1515,[[[0,0],[3,4]]],self.want(str(center)),self.record(0.1),'python')[0])
 def test_decimal_str_rounding_false_reject_counterexample(self):
  self.assertTrue(compare(1515,[[[0,0],[3,4]]],self.want('0.10001'),self.record(0.1),'python')[0])
 def test_nonfinite_bool_and_typed_integer_policy(self):
  want=self.want('5')
  for value in(True,False,float('inf'),-float('inf'),float('nan'),5):
   self.assertFalse(compare(1515,[[[0,0],[3,4]]],want,self.record(value),'python')[0])
  self.assertTrue(compare(1515,[[[0,0],[3,4]]],want,self.record(5,'number'),'javascript')[0])
  self.assertFalse(compare(1515,[[[0,0],[3,4]]],want,self.record(True,'number'),'javascript')[0])
 def test_subnormal_and_maxfinite_are_exactly_converted(self):
  for value,want,ok in((math.nextafter(0.,1.),'0',True),(float.fromhex('0x1.fffffffffffffp+1023'),'0',False)):
   self.assertEqual(compare(1515,[[[0,0],[3,4]]],self.want(want),self.record(value),'python')[0],ok)
if __name__=='__main__':unittest.main()
