"""Original candidate; no qualification or admission."""

def solve(stones,k):
    n=len(stones)
    if (n-1)%(k-1):return -1
    prefix=[0]
    for v in stones:prefix.append(prefix[-1]+v)
    dp=[[0]*n for _ in range(n)]
    for length in range(k,n+1):
        for left in range(n-length+1):
            right=left+length-1
            dp[left][right]=min(dp[left][middle]+dp[middle+1][right] for middle in range(left,right,k-1))
            if (length-1)%(k-1)==0:dp[left][right]+=prefix[right+1]-prefix[left]
    return dp[0][-1]


class Solution:
    def mergeStones(self, stones, k):
        return solve(stones, k)
