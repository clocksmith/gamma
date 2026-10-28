def solve(nums, target):
    return len({x for x, y in zip(nums, target) if x != y})


class Solution:
    def minOperations(self, nums, target):
        return solve(nums, target)
