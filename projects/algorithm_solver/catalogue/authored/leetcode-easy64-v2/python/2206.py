"""2206. Divide Array Into Equal Pairs (Easy).

Specification: https://leetcode.com/problems/divide-array-into-equal-pairs/description/
"""


def solve(nums: list[int]) -> bool:
    """O(n) expected time, O(n) space; every distinct value needs an even frequency."""
    counts = {}
    for value in nums:
        counts[value] = counts.get(value, 0) + 1
    for count in counts.values():
        if count % 2 != 0:
            return False
    return True


class Solution:
    def divideArray(self, nums: list[int]) -> bool:
        return solve(nums)
