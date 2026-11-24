# -*- coding: utf-8 -*-
import sys
sys.setrecursionlimit(10**9)
INF=10**18
MOD=10**9+7
input=lambda: sys.stdin.readline().rstrip()
YesNo=lambda b: bool([print('Yes')] if b else print('No'))
YESNO=lambda b: bool([print('YES')] if b else print('NO'))
int1=lambda x:int(x)-1

N=int(input())
T=[0]+list(map(lambda x:int(x)*2,input().split()))+[0]
V=[0]+list(map(lambda x:int(x)*2,input().split()))+[0]
v=[INF]*(sum(T)+1)
def f(v,l,r,t):
    if t<l:
        return v+(l-t)
    elif l<=t<r:
        return v
    else:
        return v+(t-r)
t=0
for i in range(N+2):
    for j in range(len(v)):
        v[j]=min(v[j],f(V[i],t,t+T[i],j))
    t+=T[i]
ans=0
for i in range(len(v)-1):
    ans+=v[i]+v[i+1]
ans/=8
print(ans)