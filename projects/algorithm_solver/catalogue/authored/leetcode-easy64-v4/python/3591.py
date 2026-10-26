"""3591. Check if Any Element Has Prime Frequency (Easy).

Specification: https://leetcode.com/problems/check-if-any-element-has-prime-frequency/description/
"""


def solve(nums: list[int]) -> bool:
    """O(n + u * sqrt(n)) time, O(u) space; u is the distinct-value count; preserve nums."""
    counts = {}
    for value in nums:
        counts[value] = counts.get(value, 0) + 1
    for count in counts.values():
        if count < 2:
            continue
        prime = True
        divisor = 2
        while divisor * divisor <= count:
            if count % divisor == 0:
                prime = False
                break
            divisor += 1
        if prime:
            return True
    return False


class Solution:
    def checkPrimeFrequency(self, nums: list[int]) -> bool:
        return solve(nums)
