"""Original candidate; no qualification or admission."""

from functools import lru_cache
from math import isqrt

def solve(nums):
    values=sorted(nums);n=len(values);adj=[[j for j in range(n) if j!=i and isqrt(values[i]+values[j])**2==values[i]+values[j]] for i in range(n)]
    @lru_cache(None)
    def count(last,mask):
        if mask==(1<<n)-1:return 1
        answer=0
        for j in (range(n) if last==-1 else adj[last]):
            if mask>>j&1 or j and values[j]==values[j-1] and not mask>>(j-1)&1:continue
            answer+=count(j,mask|(1<<j))
        return answer
    return count(-1,0)


class Solution:
    def numSquarefulPerms(self, nums):
        return solve(nums)
