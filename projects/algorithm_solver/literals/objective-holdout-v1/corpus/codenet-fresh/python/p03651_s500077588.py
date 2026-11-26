from sys import stdin
from fractions import gcd
from functools import reduce

def gcd_l(l):
    return reduce(gcd, l)

N, K = [int(_) for _ in stdin.readline().rstrip().split()]
A = [int(_) for _ in stdin.readline().rstrip().split()]
ans = gcd_l(A)
if K % ans == 0 and max(A) >= K:
    print('POSSIBLE')
else:
    print('IMPOSSIBLE')