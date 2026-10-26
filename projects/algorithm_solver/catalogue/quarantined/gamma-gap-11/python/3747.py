"""3747. Count Distinct Integers After Removing Zeros."""
from __future__ import annotations


def solve(n: int) -> int:
    """O(log n) digit steps and O(log n) space; count exactly the positive zero-free integers <= n."""
    digits = str(n)
    length = len(digits)
    answer = sum(9 ** count for count in range(1, length))
    for index, char in enumerate(digits):
        digit = int(char)
        if digit == 0:
            return answer
        answer += (digit - 1) * 9 ** (length - index - 1)
    return answer + 1


class Solution:
    def countDistinct(self, n: int) -> int:
        return solve(n)
