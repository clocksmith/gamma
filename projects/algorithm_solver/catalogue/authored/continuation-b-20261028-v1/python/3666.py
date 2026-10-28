from collections import deque

def solve(s, k):
    n = len(s)
    zeros = s.count('0')
    if zeros == 0: return 0
    parent = list(range(n+3))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    parent[zeros] = find(zeros+2)
    queue = deque([(zeros, 0)])
    while queue:
        z, steps = queue.popleft()
        lo = z+k-2*min(z,k)
        hi = z+k-2*max(0,k-(n-z))
        nxt = find(lo)
        while nxt <= hi:
            if nxt == 0: return steps+1
            queue.append((nxt, steps+1))
            parent[nxt] = find(nxt+2)
            nxt = find(nxt)
    return -1

class Solution:
    def minOperations(self, s, k):
        return solve(s, k)
