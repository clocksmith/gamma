class Solution:
    def maxNonOverlapping(self, nums: list[int], target: int) -> int:
        prefixes = {0}
        total = 0
        count = 0
        for value in nums:
            total += value
            if total - target in prefixes:
                count += 1
                total = 0
                prefixes = {0}
            else:
                prefixes.add(total)
        return count
