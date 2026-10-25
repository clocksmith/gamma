class Solution:
    def findLengthOfLCIS(self, nums: list[int]) -> int:
        longest = 0
        length = 0
        for index, value in enumerate(nums):
            if index > 0 and nums[index - 1] < value:
                length += 1
            else:
                length = 1
            longest = max(longest, length)
        return longest
