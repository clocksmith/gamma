from fractions import gcd
from math import sqrt
from heapq import *
from math import factorial
from collections import defaultdict

N,M=map(int,input().split())
S=input()
T=input()
g=gcd(N,M)
m=(N//g)*(M//g)*g
a=0
b=0
A=m//N
B=m//M
t=True
while(a<N):
    if S[a]==T[b]:
        a+=B
        b+=A
    else:
        print(-1)
        quit()
print(m)
