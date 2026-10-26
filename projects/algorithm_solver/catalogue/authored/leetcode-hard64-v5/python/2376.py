"""2376. Count Special Integers. Count unique-digit prefixes using permutations."""


def solve(n: int) -> int:
    """O(d^2+10*d) time and O(d) space for d decimal digits. Inputs are preserved."""
    digits = [int(char) for char in str(n)]
    size = len(digits)

    def permutations(available, count):
        if count > available:
            return 0
        ways = 1
        for offset in range(count):
            ways *= available - offset
        return ways

    answer = sum(9 * permutations(9, length - 1) for length in range(1, size))
    used = 0
    for index, digit in enumerate(digits):
        for smaller in range(1 if index == 0 else 0, digit):
            if used & (1 << smaller) == 0:
                answer += permutations(9 - index, size - index - 1)
        if used & (1 << digit):
            return answer
        used |= 1 << digit
    return answer + 1


class Solution:
    def countSpecialNumbers(self, n: int) -> int:
        return solve(n)
