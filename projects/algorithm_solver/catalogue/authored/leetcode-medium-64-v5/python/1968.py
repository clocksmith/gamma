"""1968. Array With Elements Not Equal to Average of Neighbors: turn a sorted copy into alternating strict peaks and valleys."""


def solve(nums: list[int]) -> list[int]:
    """O(n * log(n + 1)) time and O(n) space; inputs are read-only."""
    result = sorted(nums)
    for index in range(1, len(result) - 1, 2):
        result[index], result[index + 1] = result[index + 1], result[index]
    return result


class Solution:
    def rearrangeArray(self, nums: list[int]) -> list[int]:
        return solve(nums)
