"""Original candidate for LeetCode 2814. Contract: https://leetcode.com/problems/minimum-time-takes-to-reach-destination-without-drowning/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(mn) time and space"""
from collections import deque
def solve(land):
    m=len(land);n=len(land[0]);water=[[10**9]*n for _ in land];q=deque();start=None
    for r in range(m):
        for c in range(n):
            if land[r][c]=='*':water[r][c]=0;q.append((r,c))
            if land[r][c]=='S':start=(r,c)
    def neighbors(r,c):
        for a,b in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)):
            if 0<=a<m and 0<=b<n:yield a,b
    while q:
        r,c=q.popleft()
        for a,b in neighbors(r,c):
            if land[a][b] not in 'XD' and water[a][b]>water[r][c]+1:
                water[a][b]=water[r][c]+1;q.append((a,b))
    q=deque([(*start,0)]);seen={start}
    while q:
        r,c,t=q.popleft()
        if land[r][c]=='D':return t
        for a,b in neighbors(r,c):
            if land[a][b]!='X' and (a,b) not in seen and t+1<water[a][b]:seen.add((a,b));q.append((a,b,t+1))
    return -1
