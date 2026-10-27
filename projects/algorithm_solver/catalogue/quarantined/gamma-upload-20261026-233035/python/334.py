"""334. Increasing Triplet Subsequence."""
def solve(nums: list[int]) -> bool:
    first = second = float('inf')
    for value in nums:
        if value <= first:
            first = value
        elif value <= second:
            second = value
        else:
            return True
    return False

class Solution:
    def increasingTriplet(self, nums: list[int]) -> bool:
        return solve(nums)
