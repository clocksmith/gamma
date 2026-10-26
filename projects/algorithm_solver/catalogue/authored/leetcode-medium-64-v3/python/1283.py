"""1283. Find the Smallest Divisor Given a Threshold: binary search the first divisor whose rounded sum fits."""


def solve(nums: list[int], threshold: int) -> int:
    """O(n log M) time and O(1) auxiliary space for maximum value M; inputs are read-only."""
    low, high = 1, max(nums)
    while low < high:
        middle = (low + high) // 2
        total = 0
        for value in nums:
            total += (value + middle - 1) // middle
            if total > threshold:
                break
        if total <= threshold:
            high = middle
        else:
            low = middle + 1
    return low


class Solution:
    def smallestDivisor(self, nums: list[int], threshold: int) -> int:
        return solve(nums, threshold)
