# coding: utf-8
# Your code here!
from collections import Counter
def MI():return map(int,input().split())
def LI():return list(MI())

n=int(input())
s=input()
ans=s.count("R")*s.count("G")*s.count("B")


for j in range(n):
    jj=s[j]
    for i in range(j):
        k=2*j-i
        if not j<=k<=n-1:
            continue
        ii=s[i]
        kk=s[k]
        if jj!=ii and jj!=kk and ii!=kk:
            ans-=1

print(ans)