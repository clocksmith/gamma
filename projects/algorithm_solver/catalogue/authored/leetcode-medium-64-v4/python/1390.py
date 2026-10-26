"""1390. Four Divisors: enumerate divisor pairs and stop after the fourth divisor is exceeded."""


def solve(nums: list[int]) -> int:
    """O(n * sqrt(M)) time and O(1) auxiliary space, where M is the largest value; inputs are read-only."""
    total = 0
    for value in nums:
        count = subtotal = 0
        divisor = 1
        while divisor * divisor <= value:
            if value % divisor == 0:
                partner = value // divisor
                if partner == divisor:
                    count += 1
                    subtotal += divisor
                else:
                    count += 2
                    subtotal += divisor + partner
                if count > 4:
                    break
            divisor += 1
        if count == 4:
            total += subtotal
    return total


class Solution:
    def sumFourDivisors(self, nums: list[int]) -> int:
        return solve(nums)
