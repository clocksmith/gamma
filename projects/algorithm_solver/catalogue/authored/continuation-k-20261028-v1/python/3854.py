def solve(nums):
    if len(nums) == 1:
        return [0, 0]
    best = None
    for first in (0, 1):
        operations = 0
        lower = -10**20
        upper = 10**20
        for i, x in enumerate(nums):
            wrong = int(x % 2 != (first + i) % 2)
            operations += wrong
            lower = max(lower, x - wrong)
            upper = min(upper, x + wrong)
        result = (operations, max(1, lower - upper))
        if best is None or result < best:
            best = result
    return list(best)


class Solution:
    def makeParityAlternating(self, nums):
        return solve(nums)
