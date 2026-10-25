"""2520. Count the Digits That Divide a Number (Easy).

Specification: https://leetcode.com/problems/count-the-digits-that-divide-a-number/description/
"""


def solve(num: int) -> int:
    """O(log num) time, O(1) space; count each dividing digit occurrence."""
    remaining = num
    count = 0
    while remaining > 0:
        digit = remaining % 10
        if digit != 0 and num % digit == 0:
            count += 1
        remaining //= 10
    return count


class Solution:
    def countDigits(self, num: int) -> int:
        return solve(num)
