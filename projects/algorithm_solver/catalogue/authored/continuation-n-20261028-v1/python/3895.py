"""Original frontend 3895 variant; qualification unknown."""

def solve(nums, digit):
    total = 0
    for value in nums:
        while value:
            total += value % 10 == digit
            value //= 10
    return total


class Solution:
    def countDigitOccurrences(self, nums, digit):
        return solve(nums, digit)
