class Solution:
    def sortArrayByParityII(self, nums: list[int]) -> list[int]:
        result = [0] * len(nums)
        even = 0
        odd = 1
        for value in nums:
            if value % 2 == 0:
                result[even] = value
                even += 2
            else:
                result[odd] = value
                odd += 2
        return result
