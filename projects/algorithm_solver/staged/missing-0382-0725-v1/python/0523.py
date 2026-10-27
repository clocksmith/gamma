"""523. Continuous Subarray Sum."""

def solve(nums: list[int], k: int) -> bool:
    first = {0: -1}
    total = 0
    for index, value in enumerate(nums):
        total += value
        remainder = total % abs(k) if k else total
        if remainder in first:
            if index - first[remainder] >= 2:
                return True
        else:
            first[remainder] = index
    return False


class Solution:
    def checkSubarraySum(self, nums: list[int], k: int) -> bool:
        return solve(nums, k)
