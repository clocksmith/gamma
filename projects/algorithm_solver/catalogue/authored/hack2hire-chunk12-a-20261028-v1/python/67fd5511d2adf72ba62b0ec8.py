"""Hack2Hire 67fd5511d2adf72ba62b0ec8 (Max Fly Distance) over an INFERRED spec; qualification unknown."""


_NEG = -(1 << 62)  # unreachable energy level; real distances are at most 1e14


def solve(arr, k):
    if k == 0:
        return 0
    if k >= len(arr):
        return sum(arr)
    dp = [_NEG] * k + [0]  # dp[e]: best distance with energy e
    for a in arr:
        fly = [d + a for d in dp[1:]] + [_NEG]
        rest = [_NEG] + dp[:k - 1] + [max(dp[k - 1], dp[k])]
        dp = [f if f > r else r for f, r in zip(fly, rest)]
    return max(dp)


class Solution:
    def maxFlyDistance(self, arr, k):
        return solve(arr, k)
