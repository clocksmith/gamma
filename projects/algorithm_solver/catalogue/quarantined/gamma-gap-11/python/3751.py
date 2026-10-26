"""3751. Total Waviness of Numbers in Range I."""
from __future__ import annotations


def solve(num1: int, num2: int) -> int:
    """O((num2 - num1 + 1) log num2) time and O(log num2) auxiliary space; num2 <= 1e5."""
    answer = 0
    for value in range(num1, num2 + 1):
        digits = str(value)
        for index in range(1, len(digits) - 1):
            if (digits[index] > digits[index - 1] and digits[index] > digits[index + 1]) or (digits[index] < digits[index - 1] and digits[index] < digits[index + 1]):
                answer += 1
    return answer


class Solution:
    def totalWaviness(self, num1: int, num2: int) -> int:
        return solve(num1, num2)
