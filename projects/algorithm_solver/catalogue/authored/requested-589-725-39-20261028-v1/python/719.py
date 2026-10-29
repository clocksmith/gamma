"""Original LeetCode 719 candidate; qualification unknown."""

def solve(nums, k):
    values = sorted(nums)
    low, high = 0, values[-1] - values[0]
    while low < high:
        distance = (low + high) // 2
        left = count = 0
        for right, value in enumerate(values):
            while value - values[left] > distance: left += 1
            count += right - left
        if count >= k: high = distance
        else: low = distance + 1
    return low


class Solution:
    def smallestDistancePair(self, nums, k):
        return solve(nums, k)
