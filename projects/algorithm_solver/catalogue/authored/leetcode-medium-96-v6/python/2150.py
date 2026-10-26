"""2150. Find All Lonely Numbers in the Array: retain unique values whose two neighboring integers are absent."""
from collections import Counter


def solve(nums: list[int]) -> list[int]:
    """O(n) expected time and O(n) auxiliary and result space; inputs are read-only."""
    counts = Counter(nums)
    return [value for value in nums
            if counts[value] == 1 and value - 1 not in counts and value + 1 not in counts]


class Solution:
    def findLonely(self, nums: list[int]) -> list[int]:
        return solve(nums)
