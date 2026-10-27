"""75. Sort Colors."""
def solve(nums: list[int]) -> None:
    low = current = 0
    high = len(nums) - 1
    while current <= high:
        if nums[current] == 0:
            nums[low], nums[current] = nums[current], nums[low]
            low += 1
            current += 1
        elif nums[current] == 2:
            nums[current], nums[high] = nums[high], nums[current]
            high -= 1
        else:
            current += 1

class Solution:
    def sortColors(self, nums: list[int]) -> None:
        solve(nums)
