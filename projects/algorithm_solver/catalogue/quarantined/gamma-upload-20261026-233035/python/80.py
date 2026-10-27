"""80. Remove Duplicates from Sorted Array II."""
def solve(nums: list[int]) -> int:
    write = 0
    for value in nums:
        if write < 2 or nums[write - 2] != value:
            nums[write] = value
            write += 1
    return write

class Solution:
    def removeDuplicates(self, nums: list[int]) -> int:
        return solve(nums)
