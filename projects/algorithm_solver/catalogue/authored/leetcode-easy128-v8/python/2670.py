"""2670. Find the Distinct Difference Array (Easy).

Specification: https://leetcode.com/problems/find-the-distinct-difference-array/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n) expected time, O(n) space; maintain prefix membership and remaining suffix frequencies."""
    suffix = {}
    for value in nums:
        suffix[value] = suffix.get(value, 0) + 1
    prefix = set()
    result = []
    for value in nums:
        prefix.add(value)
        suffix[value] -= 1
        if suffix[value] == 0:
            del suffix[value]
        result.append(len(prefix) - len(suffix))
    return result


class Solution:
    def distinctDifferenceArray(self, nums: list[int]) -> list[int]:
        return solve(nums)
