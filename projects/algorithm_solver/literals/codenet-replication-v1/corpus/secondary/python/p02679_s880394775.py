import sys
import math
from fractions import Fraction
input = sys.stdin.readline
sys.setrecursionlimit(10**7)
from collections import defaultdict

MOD = 10**9+7
N = int(input())
dic = defaultdict(int)
gp = []
zero = 0
left_zero = 0
right_zero = 0
for i in range(N):
    a,b = map(int, input().split())
    if b < 0:
        a = -a
        b = -b
    if a == 0 and b != 0:
        left_zero += 1
    elif a != 0 and b == 0:
        right_zero += 1
    elif a == 0 and b == 0:
        zero += 1
    else:
        g = math.gcd(a, b)
        a //= g
        b //= g
        dic[str(Fraction(a, b))] += 1
        gp.append((a, b))
done = defaultdict(bool)
ans = 1
for a,b in gp:
    k = str(Fraction(a, b))
    if done[k]: continue
    rk = str(Fraction(-b, a))
    done[k] = True
    done[rk] = True
    cnt1 = pow(2, dic[k], MOD)-1
    cnt2 = pow(2, dic[rk], MOD)-1
    c = cnt1+cnt2+1
    ans *= c
    ans %= MOD
c1 = pow(2, left_zero, MOD)-1
c2 = pow(2, right_zero, MOD)-1
c = c1+c2+1
ans *= c
ans += zero
ans %= MOD
print((ans-1)%MOD)
