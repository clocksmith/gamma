"""507. Perfect Number (Easy).

Specification: https://leetcode.com/problems/perfect-number/description/
"""


def solve(num: int) -> bool:
    """O(sqrt(num)) time, O(1) space; count each proper-divisor pair once."""
    if num <= 1:
        return False
    total = 1
    divisor = 2
    while divisor * divisor <= num:
        if num % divisor == 0:
            total += divisor
            partner = num // divisor
            if partner != divisor:
                total += partner
        divisor += 1
    return total == num


class Solution:
    def checkPerfectNumber(self, num: int) -> bool:
        return solve(num)
