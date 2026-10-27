# Original candidate implementation. Contract: https://leetcode.com/problems/maximum-hamming-distances/
from collections import deque

def solve(nums,m):
    size=1<<m;dist=[-1]*size;queue=deque()
    for v in nums:
        if dist[v]<0:dist[v]=0;queue.append(v)
    while queue:
        v=queue.popleft()
        for bit in range(m):
            w=v^(1<<bit)
            if dist[w]<0:dist[w]=dist[v]+1;queue.append(w)
    return [m-dist[(size-1)^v] for v in nums]
