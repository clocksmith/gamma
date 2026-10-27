"""283. Move Zeroes."""
def solve(nums: list[int]) -> None:
    write = 0
    for value in nums:
        if value != 0:
            nums[write] = value
            write += 1
    while write < len(nums):
        nums[write] = 0
        write += 1

class Solution:
    def moveZeroes(self, nums: list[int]) -> None:
        solve(nums)
