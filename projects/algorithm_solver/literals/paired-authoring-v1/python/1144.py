class Solution:
    def movesToMakeZigzag(self, nums: list[int]) -> int:
        costs = [0, 0]
        for index, value in enumerate(nums):
            decrease = 0
            if index > 0:
                decrease = max(decrease, value - nums[index - 1] + 1)
            if index + 1 < len(nums):
                decrease = max(decrease, value - nums[index + 1] + 1)
            costs[index % 2] += decrease
        return min(costs)
