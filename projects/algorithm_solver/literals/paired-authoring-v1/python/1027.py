class Solution:
    def longestArithSeqLength(self, nums):
        if len(nums) < 2:
            return len(nums)
        ending = [{} for _ in nums]
        best = 2
        for right in range(len(nums)):
            for left in range(right):
                difference = nums[right] - nums[left]
                length = ending[left].get(difference, 1) + 1
                ending[right][difference] = max(ending[right].get(difference, 0), length)
                best = max(best, ending[right][difference])
        return best
