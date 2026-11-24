"""from collections import *
from itertools import *
from bisect import *
from heapq import *

import math
from fractions import gcd"""
N,K=map(int,input().split())

#A=[list(reversed(list(map(int,input().split())))) for i in range(N)]
A=list(map(int,input().split()))
A.sort()
mod=10**9+7
fac=[1,1]
for i in range(2,N+1):
    fac.append(fac[i-1]*i%mod)
ifac=[pow(i,mod-2,mod) for i in fac]


if K==1:
    print(0)
    exit()


count=0
ncount=0
for i in range(N-K+1):
    n=N-i-K
    m=i+K-2
    ncount+=fac[m]*ifac[K-2]*ifac[m-(K-2)]%mod
    ncount%=mod
    count-=A[n]*ncount
    count%=mod

ncount=0
for i in range(K-1,N):
    n=i-1
    ncount+=fac[n]*ifac[K-2]*ifac[n-(K-2)]%mod
    ncount%=mod
    count+=A[i]*ncount
    count%=mod
print(count)
