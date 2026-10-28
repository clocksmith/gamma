"""2784. Check if Array is Good (Easy).

Specification: https://leetcode.com/problems/check-if-array-is-good/description/
"""


def solve(nums: list[int]) -> bool:
    n = len(nums) - 1
    if n < 1:
        return False
    freq = {}
    for x in nums:
        freq[x] = freq.get(x, 0) + 1
    if len(freq) != n:
        return False
    for v in range(1, n + 1):
        want = 2 if v == n else 1
        if freq.get(v) != want:
            return False
    return True


class Solution:
    def isGood(self, nums: list[int]) -> bool:
        return solve(nums)
