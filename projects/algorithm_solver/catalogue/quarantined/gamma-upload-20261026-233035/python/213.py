"""213. House Robber II."""
def linear(nums: list[int]) -> int:
    previous = current = 0
    for value in nums:
        previous, current = current, max(current, previous + value)
    return current

def solve(nums: list[int]) -> int:
    return nums[0] if len(nums) == 1 else max(linear(nums[:-1]), linear(nums[1:]))

class Solution:
    def rob(self, nums: list[int]) -> int:
        return solve(nums)
