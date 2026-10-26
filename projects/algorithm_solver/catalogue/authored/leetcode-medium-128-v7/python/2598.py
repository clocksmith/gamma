"""2598. Smallest Missing Non-negative Integer After Operations: consume available residue classes in increasing target order."""
from collections import Counter


def solve(nums: list[int], value: int) -> int:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    counts = Counter(number % value for number in nums)
    result = 0
    while counts[result % value] > 0:
        counts[result % value] -= 1
        result += 1
    return result


class Solution:
    def findSmallestInteger(self, nums: list[int], value: int) -> int:
        return solve(nums, value)
