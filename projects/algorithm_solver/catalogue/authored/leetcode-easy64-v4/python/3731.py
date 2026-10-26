"""3731. Find Missing Elements (Easy).

Specification: https://leetcode.com/problems/find-missing-elements/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n + R) expected time, O(n + R) space; R is the value range; preserve nums."""
    present = set(nums)
    smallest = min(nums)
    largest = max(nums)
    result = []
    for value in range(smallest, largest + 1):
        if value not in present:
            result.append(value)
    return result


class Solution:
    def findMissingElements(self, nums: list[int]) -> list[int]:
        return solve(nums)
