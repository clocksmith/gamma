"""2341. Maximum Number of Pairs in Array (Easy).

Specification: https://leetcode.com/problems/maximum-number-of-pairs-in-array/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n) expected time, O(u) space; match each new value against an unmatched equal value."""
    unmatched = set()
    pairs = 0
    for value in nums:
        if value in unmatched:
            unmatched.remove(value)
            pairs += 1
        else:
            unmatched.add(value)
    return [pairs, len(unmatched)]


class Solution:
    def numberOfPairs(self, nums: list[int]) -> list[int]:
        return solve(nums)
