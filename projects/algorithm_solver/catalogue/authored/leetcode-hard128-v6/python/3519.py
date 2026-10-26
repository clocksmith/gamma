"""3519. Count Numbers with Non-Decreasing Digits.

Convert decimal bounds exactly and count bounded non-decreasing base-b digits; O(L*b^2) digit-DP time and O(L+b) space, excluding big-integer conversion. Inputs are preserved.
"""

def solve(l: str, r: str, b: int) -> int:
    modulus = 1_000_000_007

    def count_through(bound):
        if bound < 0:
            return 0
        digits = []
        while bound:
            bound, digit = divmod(bound, b)
            digits.append(digit)
        digits = digits[::-1] or [0]
        ways = [[0, 0] for _ in range(b)]
        ways[0][1] = 1
        for limit_digit in digits:
            following = [[0, 0] for _ in range(b)]
            for previous in range(b):
                for tight in range(2):
                    count = ways[previous][tight]
                    if not count:
                        continue
                    limit = limit_digit if tight else b - 1
                    for digit in range(previous, limit + 1):
                        next_tight = int(tight and digit == limit_digit)
                        following[digit][next_tight] = (following[digit][next_tight] + count) % modulus
            ways = following
        return sum(sum(row) for row in ways) % modulus

    return (count_through(int(r)) - count_through(int(l) - 1)) % modulus


class Solution:
    def countNumbers(self, l: str, r: str, b: int) -> int:
        return solve(l, r, b)
