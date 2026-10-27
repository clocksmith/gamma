# Original implementation. Contract: https://leetcode.com/problems/minimum-number-of-lines-to-cover-points/
from functools import lru_cache
def solve(points):
    n=len(points);masks=[[0]*n for _ in range(n)]
    for i,(x,y) in enumerate(points):
        for j,(u,v) in enumerate(points):
            if i!=j:
                masks[i][j]=sum(1<<k for k,(a,b) in enumerate(points) if (a-x)*(v-y)==(b-y)*(u-x))
    @lru_cache(None)
    def dp(mask):
        if not mask:return 0
        bit=mask&-mask;i=bit.bit_length()-1;best=1+dp(mask^bit)
        for j in range(i+1,n):
            if mask>>j&1:best=min(best,1+dp(mask&~masks[i][j]))
        return best
    return dp((1<<n)-1)
