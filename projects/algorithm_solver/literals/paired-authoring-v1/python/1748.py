class Solution:
    def sumOfUnique(self, nums: list[int]) -> int:
        counts = {}
        for value in nums:
            counts[value] = counts.get(value, 0) + 1
        total = 0
        for value, count in counts.items():
            if count == 1:
                total += value
        return total
