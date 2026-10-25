class Solution:
    def sortArrayByParityII(self, nums: list[int]) -> list[int]:
        odd = 1
        for even in range(0, len(nums), 2):
            if nums[even] % 2 != 0:
                while odd < len(nums) and nums[odd] % 2 != 0:
                    odd += 2
                nums[even], nums[odd] = nums[odd], nums[even]
        return nums
