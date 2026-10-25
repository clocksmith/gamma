class Solution:
    def findMaxAverage(self, nums: list[int], k: int) -> float:
        total = 0
        for index in range(k):
            total += nums[index]
        best = total
        for index in range(k, len(nums)):
            total -= nums[index - k]
            total += nums[index]
            best = max(best, total)
        return best / k
