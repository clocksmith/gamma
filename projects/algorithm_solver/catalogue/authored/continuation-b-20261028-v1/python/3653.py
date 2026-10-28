def solve(nums, queries):
    values = nums[:]
    modulus = 1000000007
    for left, right, step, multiplier in queries:
        for i in range(left, right+1, step): values[i] = values[i]*multiplier % modulus
    result = 0
    for value in values: result ^= value
    return result

class Solution:
    def xorAfterQueries(self, nums, queries):
        return solve(nums, queries)
