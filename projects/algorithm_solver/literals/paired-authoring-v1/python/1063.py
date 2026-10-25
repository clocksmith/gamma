class Solution:
    def validSubarrays(self, nums):
        starts = []
        total = 0
        for value in nums:
            while starts and starts[-1] > value:
                starts.pop()
            starts.append(value)
            total += len(starts)
        return total
