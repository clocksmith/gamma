"""Original frontend 3824 variant; qualification unknown."""

def solve(nums):
    low, high = 1, max(max(nums), len(nums))
    while low < high:
        middle = (low + high) // 2
        operations = sum((value + middle - 1) // middle for value in nums)
        if operations <= middle * middle:
            high = middle
        else:
            low = middle + 1
    return low


class Solution:
    def minimumK(self, nums):
        return solve(nums)
