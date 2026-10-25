class Solution:
    def findLHS(self, nums: list[int]) -> int:
        counts = {}
        for value in nums:
            counts[value] = counts.get(value, 0) + 1
        longest = 0
        for value, count in counts.items():
            if value + 1 in counts:
                longest = max(longest, count + counts[value + 1])
        return longest
