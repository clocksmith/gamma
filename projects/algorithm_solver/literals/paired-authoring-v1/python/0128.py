class Solution:
    def longestConsecutive(self, nums: list[int]) -> int:
        values = set(nums)
        longest = 0
        for value in values:
            if value - 1 in values:
                continue
            current = value
            length = 1
            while current + 1 in values:
                current += 1
                length += 1
            longest = max(longest, length)
        return longest
