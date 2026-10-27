"""324. Wiggle Sort II."""
def solve(nums: list[int]) -> None:
    values = sorted(nums)
    small = (len(nums) - 1) // 2
    large = len(nums) - 1
    for index in range(len(nums)):
        if index % 2 == 0:
            nums[index] = values[small]
            small -= 1
        else:
            nums[index] = values[large]
            large -= 1

class Solution:
    def wiggleSort(self, nums: list[int]) -> None:
        solve(nums)
