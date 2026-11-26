#D
from heapq import heappush,heappop
from collections import deque
import sys
n,k=map(int,input().split())
v=deque(list(map(int,input().split())))
w=[[] for i in range(n)]
answer=-100000000
for i in range(min(n+1,k+1)):
    for j in range(min(n-i+1,k-i+1)):
        h=[]
        
        for a in range(i):
            heappush(h,v[a])
        for a in range(j):
            heappush(h,v[n-1-a])
        for a in range(k-i-j):
            if h and h[0]<0:
                heappop(h)
            else:
                break
        answer=max(answer,sum(h))
print(answer)