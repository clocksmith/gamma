"""2453. Destroy Sequential Targets: choose the smallest target in a largest residue class."""
from collections import Counter


def solve(nums: list[int], space: int) -> int:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    counts = Counter(value % space for value in nums)
    answer = nums[0]
    best_count = 0
    for value in nums:
        count = counts[value % space]
        if count > best_count or (count == best_count and value < answer):
            answer, best_count = value, count
    return answer


class Solution:
    def destroyTargets(self, nums: list[int], space: int) -> int:
        return solve(nums, space)
