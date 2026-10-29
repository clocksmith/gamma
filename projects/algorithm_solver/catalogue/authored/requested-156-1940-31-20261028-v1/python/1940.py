"""Original frontend 1940 variant; qualification unknown."""

from collections import Counter


def solve(arrays):
    m = len(arrays)
    cnt = Counter(x for arr in arrays for x in arr)
    return [x for x in arrays[0] if cnt[x] == m]


longestCommonSubsequence = solve


class Solution:
    def longestCommonSubsequence(self, arrays):
        return solve(arrays)
