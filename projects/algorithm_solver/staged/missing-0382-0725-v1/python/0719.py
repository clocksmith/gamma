"""719. Find K-th Smallest Pair Distance."""

def solve(nums: list[int], k: int) -> int:
    ordered = sorted(nums)
    low, high = 0, ordered[-1] - ordered[0]
    while low < high:
        middle = (low + high) // 2
        left = count = 0
        for right in range(len(ordered)):
            while ordered[right] - ordered[left] > middle:
                left += 1
            count += right - left
        if count >= k:
            high = middle
        else:
            low = middle + 1
    return low


class Solution:
    def smallestDistancePair(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
