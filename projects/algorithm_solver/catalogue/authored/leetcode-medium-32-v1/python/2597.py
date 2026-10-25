"""2597. The Number of Beautiful Subsets: combine independent residue groups with skip/take dynamic programming."""
from collections import Counter


def solve(nums: list[int], k: int) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    groups = {}
    for value, frequency in Counter(nums).items():
        groups.setdefault(value % k, []).append((value, frequency))
    answer = 1
    for group in groups.values():
        group.sort()
        skipped = 1
        taken = 0
        previous = None
        for value, frequency in group:
            choices = (1 << frequency) - 1
            total = skipped + taken
            available = skipped if previous is not None and value - previous == k else total
            next_taken = choices * available
            skipped, taken = total, next_taken
            previous = value
        answer *= skipped + taken
    return answer - 1


class Solution:
    def beautifulSubsets(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
