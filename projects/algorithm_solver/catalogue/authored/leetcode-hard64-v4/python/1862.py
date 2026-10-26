"""1862. Sum of Floored Pairs."""


def solve(nums: list[int]) -> int:
    """Frequency prefix sums over quotient ranges; O(n+M log M) time and O(M) space. Inputs are preserved."""
    modulus = 1_000_000_007
    maximum = max(nums)
    frequency = [0] * (maximum + 1)
    for value in nums:
        frequency[value] += 1
    prefix = [0] * (maximum + 1)
    for value in range(1, maximum + 1):
        prefix[value] = prefix[value - 1] + frequency[value]
    answer = 0
    for denominator in range(1, maximum + 1):
        if frequency[denominator] == 0:
            continue
        for left in range(denominator, maximum + 1, denominator):
            right = min(maximum, left + denominator - 1)
            amount = prefix[right] - prefix[left - 1]
            answer = (answer + frequency[denominator] * amount * (left // denominator)) % modulus
    return answer


class Solution:
    def sumOfFlooredPairs(self, nums: list[int]) -> int:
        return solve(nums)
