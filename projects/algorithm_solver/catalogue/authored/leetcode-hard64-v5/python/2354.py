"""2354. Number of Excellent Pairs. Count ordered value pairs after deduplication by population count."""


def solve(nums: list[int], k: int) -> int:
    """O(n*B+B^2) time and O(n+B) space, B=31. Inputs are preserved."""
    counts = [0] * 32
    for value in set(nums):
        counts[value.bit_count()] += 1
    answer = 0
    for first in range(32):
        for second in range(max(0, k - first), 32):
            answer += counts[first] * counts[second]
    return answer


class Solution:
    def countExcellentPairs(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
