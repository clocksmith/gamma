"""96. Unique Binary Search Trees (Medium).

Specification: https://leetcode.com/problems/unique-binary-search-trees/description/
"""


def solve(n: int) -> int:
    dp = [0] * (n + 1)
    dp[0] = 1
    if n >= 1:
        dp[1] = 1
    for nodes in range(2, n + 1):
        for root in range(1, nodes + 1):
            dp[nodes] += dp[root - 1] * dp[nodes - root]
    return dp[n]


class Solution:
    def numTrees(self, n: int) -> int:
        return solve(n)
