"""644. Maximum Average Subarray II. Binary search the answer using a minimum-prefix feasibility check for lengths at least k."""

def solve(nums: list[int], k: int) -> float:
    def feasible(average):
        total = sum(nums[:k]) - average * k
        if total >= 0:
            return True
        prefix = minimum_prefix = 0.0
        for i in range(k, len(nums)):
            total += nums[i] - average
            prefix += nums[i - k] - average
            minimum_prefix = min(minimum_prefix, prefix)
            if total - minimum_prefix >= 0:
                return True
        return False
    low, high = float(min(nums)), float(max(nums))
    for _ in range(60):
        middle = (low + high) / 2
        if feasible(middle):
            low = middle
        else:
            high = middle
    return low


class Solution:
    def findMaxAverage(self, nums: list[int], k: int) -> float:
        return solve(nums, k)
