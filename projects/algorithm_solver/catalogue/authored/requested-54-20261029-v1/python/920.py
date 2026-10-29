"""Original development candidate; independent qualification pending."""
def solve(n, goal, k):
    mod = 1000000007
    dp = [1]+[0]*n
    for _ in range(goal):
        nxt = [0]*(n+1)
        for used in range(1,n+1):
            nxt[used] = (dp[used-1]*(n-used+1)+dp[used]*max(0,used-k)) % mod
        dp = nxt
    return dp[n]


class Solution:
    def numMusicPlaylists(self, n, goal, k):
        return solve(n, goal, k)
