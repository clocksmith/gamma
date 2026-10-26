"""813. Largest Sum of Averages: partition positive prefixes with rolling dynamic programming."""


def solve(nums: list[int], k: int) -> float:
    """O(k * n^2) time and O(n) auxiliary space; inputs are read-only."""
    size = len(nums)
    prefix = [0] * (size + 1)
    for index, value in enumerate(nums):
        prefix[index + 1] = prefix[index] + value
    previous = [0.0] + [prefix[end] / end for end in range(1, size + 1)]
    # Positive values make an optimal partition use all k available groups.
    for groups in range(2, k + 1):
        current = [float('-inf')] * (size + 1)
        for end in range(groups, size + 1):
            for split in range(groups - 1, end):
                candidate = previous[split] + (prefix[end] - prefix[split]) / (end - split)
                current[end] = max(current[end], candidate)
        previous = current
    return previous[size]


class Solution:
    def largestSumOfAverages(self, nums: list[int], k: int) -> float:
        return solve(nums, k)
