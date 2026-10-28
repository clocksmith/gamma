"""Original frontend 3867 variant; qualification unknown."""

def solve(nums):
    from math import gcd
    values = []
    maximum = 0
    for value in nums:
        maximum = max(maximum, value)
        values.append(gcd(value, maximum))
    values.sort()
    return sum(gcd(values[i], values[-1 - i]) for i in range(len(values) // 2))


class Solution:
    def gcdSum(self, nums):
        return solve(nums)
