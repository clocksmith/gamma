"""2006. Count Number of Pairs With Absolute Difference K (Easy).

Specification: https://leetcode.com/problems/count-number-of-pairs-with-absolute-difference-k/description/
"""


def solve(nums: list[int], k: int) -> int:
    freq = {}
    ans = 0
    for x in nums:
        if k == 0:
            ans += freq.get(x, 0)
        else:
            ans += freq.get(x - k, 0) + freq.get(x + k, 0)
        freq[x] = freq.get(x, 0) + 1
    return ans


class Solution:
    def countKDifference(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
