class Solution:
    def minimumOperations(self, nums: list[int]) -> int:
        positive = set()
        for value in nums:
            if value > 0:
                positive.add(value)
        return len(positive)
