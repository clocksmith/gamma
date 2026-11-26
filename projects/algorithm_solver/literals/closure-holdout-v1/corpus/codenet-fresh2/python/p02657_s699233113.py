a,b = map(float,input().split())
from fractions import Fraction
import math
print(math.floor(Fraction(a)*Fraction(b)))