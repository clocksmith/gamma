class Solution:
    def findSubarrays(self, nums: list[int]) -> bool:
        seen = set()
        for index in range(1, len(nums)):
            total = nums[index - 1] + nums[index]
            if total in seen:
                return True
            seen.add(total)
        return False
