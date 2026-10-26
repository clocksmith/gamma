"""1296. Divide Array in Sets of K Consecutive Numbers: consume consecutive runs beginning at the smallest remaining value."""
from collections import Counter


def solve(nums: list[int], k: int) -> bool:
    """O(n log(n + 1)) time and O(n) auxiliary space; inputs are read-only."""
    if len(nums) % k:
        return False
    counts = Counter(nums)
    for start in sorted(counts):
        copies = counts[start]
        if not copies:
            continue
        for value in range(start, start + k):
            if counts[value] < copies:
                return False
            counts[value] -= copies
    return True


class Solution:
    def isPossibleDivide(self, nums: list[int], k: int) -> bool:
        return solve(nums, k)
