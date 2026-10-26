"""202. Happy Number (Easy).

Specification: https://leetcode.com/problems/happy-number/description/
"""


def solve(n: int) -> bool:
    """O(log n) initial digit work and bounded subsequent states for the 32-bit domain."""
    seen = set()
    current = n
    while current != 1 and current not in seen:
        seen.add(current)
        next_value = 0
        while current > 0:
            digit = current % 10
            next_value += digit * digit
            current //= 10
        current = next_value
    return current == 1


class Solution:
    def isHappy(self, n: int) -> bool:
        return solve(n)
