"""3745. Maximize Expression of Three Elements (Easy).

Specification: https://leetcode.com/problems/maximize-expression-of-three-elements/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; track two maximum occurrences and one minimum; preserve nums."""
    largest = float('-inf')
    secondLargest = float('-inf')
    smallest = float('inf')
    for value in nums:
        smallest = min(smallest, value)
        if value >= largest:
            secondLargest = largest
            largest = value
        elif value > secondLargest:
            secondLargest = value
    return largest + secondLargest - smallest


class Solution:
    def maximizeExpressionOfThree(self, nums: list[int]) -> int:
        return solve(nums)
