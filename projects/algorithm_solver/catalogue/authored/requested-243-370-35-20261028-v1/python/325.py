"""Original frontend 325 variant; qualification unknown."""


def solve(nums, k: int) -> int:
    first = {0: -1}
    cur = 0
    best = 0
    for i, x in enumerate(nums):
        cur += x
        if cur - k in first:
            if i - first[cur - k] > best:
                best = i - first[cur - k]
        if cur not in first:
            first[cur] = i
    return best


maxSubArrayLen = solve


class Solution:
    def maxSubArrayLen(self, nums, k: int) -> int:
        return solve(nums, k)
