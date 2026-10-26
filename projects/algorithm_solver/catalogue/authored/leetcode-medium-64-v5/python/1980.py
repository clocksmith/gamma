"""1980. Find Unique Binary String: differ from each input string at its own diagonal position."""


def solve(nums: list[str]) -> str:
    """O(n) time and O(n) output construction space; inputs are read-only."""
    return ''.join('1' if value[index] == '0' else '0' for index, value in enumerate(nums))


class Solution:
    def findDifferentBinaryString(self, nums: list[str]) -> str:
        return solve(nums)
