"""280. Wiggle Sort."""
def solve(nums: list[int]) -> None:
    values = sorted(nums)
    middle = (len(nums) + 1) // 2
    small = values[:middle][::-1]
    large = values[middle:][::-1]
    nums[::2] = small
    nums[1::2] = large

class Solution:
    def wiggleSort(self, nums: list[int]) -> None:
        solve(nums)
