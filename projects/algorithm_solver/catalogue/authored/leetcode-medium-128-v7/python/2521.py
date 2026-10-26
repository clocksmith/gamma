"""2521. Distinct Prime Factors of Product of Array: factor each input separately and collect its distinct prime divisors."""


def solve(nums: list[int]) -> int:
    """O(n * sqrt(M)) time and O(n log(M + 1)) auxiliary space, where M is the largest value; inputs are read-only."""
    primes = set()
    for original in nums:
        value = original
        factor = 2
        while factor * factor <= value:
            if value % factor == 0:
                primes.add(factor)
                while value % factor == 0:
                    value //= factor
            factor += 1
        if value > 1:
            primes.add(value)
    return len(primes)


class Solution:
    def distinctPrimeFactors(self, nums: list[int]) -> int:
        return solve(nums)
