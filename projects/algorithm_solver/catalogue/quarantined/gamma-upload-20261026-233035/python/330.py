"""330. Patching Array."""
def solve(nums: list[int], n: int) -> int:
    covered = 1
    index = patches = 0
    while covered <= n:
        if index < len(nums) and nums[index] <= covered:
            covered += nums[index]
            index += 1
        else:
            covered += covered
            patches += 1
    return patches

class Solution:
    def minPatches(self, nums: list[int], n: int) -> int:
        return solve(nums, n)
