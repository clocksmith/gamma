class Solution:
    def smallestRangeII(self, nums: list[int], k: int) -> int:
        ordered = sorted(nums)
        best = ordered[-1] - ordered[0]
        for index in range(len(ordered) - 1):
            highest = max(ordered[-1] - k, ordered[index] + k)
            lowest = min(ordered[0] + k, ordered[index + 1] - k)
            best = min(best, highest - lowest)
        return best
