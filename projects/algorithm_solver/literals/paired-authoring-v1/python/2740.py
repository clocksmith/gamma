class Solution:
    def findValueOfPartition(self, nums: list[int]) -> int:
        ordered = sorted(nums)
        best = ordered[1] - ordered[0]
        for index in range(2, len(ordered)):
            best = min(best, ordered[index] - ordered[index - 1])
        return best
