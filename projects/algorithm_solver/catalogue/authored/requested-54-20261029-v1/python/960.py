"""Original development candidate; independent qualification pending."""
def solve(strs):
    width = len(strs[0])
    dp = [1]*width
    for j in range(width):
        for i in range(j):
            if all(row[i] <= row[j] for row in strs):
                dp[j] = max(dp[j],dp[i]+1)
    return width-max(dp)


class Solution:
    def minDeletionSize(self, strs):
        return solve(strs)
