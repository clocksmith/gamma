"""Original candidate; no qualification or admission."""

def solve(stones):
    a=sorted(stones);n=len(a);maximum=max(a[-1]-a[1],a[-2]-a[0])-(n-2);minimum=n;left=0
    for right in range(n):
        while a[right]-a[left]+1>n:left+=1
        size=right-left+1
        candidate=2 if size==n-1 and a[right]-a[left]==n-2 else n-size
        minimum=min(minimum,candidate)
    return [minimum,maximum]


class Solution:
    def numMovesStonesII(self, stones):
        return solve(stones)
