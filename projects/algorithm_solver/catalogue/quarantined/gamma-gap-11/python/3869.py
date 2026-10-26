"""3869. Count Fancy Numbers in a Range."""
from __future__ import annotations


def solve(l: int, r: int) -> int:
    """O(100 D^2 + 10*2^10) time and O(D + 2^10) space; digit-sum DP plus deduplicated strictly monotone numbers."""
    def good(value):
        digits = str(value)
        return all(digits[index - 1] < digits[index] for index in range(1, len(digits))) or all(digits[index - 1] > digits[index] for index in range(1, len(digits)))

    monotone = set()
    for mask in range(1, 1 << 10):
        digits = [str(digit) for digit in range(10) if mask & (1 << digit)]
        if digits[0] != '0':
            monotone.add(int(''.join(digits)))
        if digits[-1] != '0':
            monotone.add(int(''.join(reversed(digits))))
    extra = [(value, good(sum(map(int, str(value))))) for value in monotone]

    def count(bound):
        if bound <= 0:
            return 0
        digits = list(map(int, str(bound)))
        limit = 9 * len(digits)
        loose = [0] * (limit + 1)
        tight = [0] * (limit + 1)
        tight[0] = 1
        for position, digit in enumerate(digits):
            next_loose = [0] * (limit + 1)
            next_tight = [0] * (limit + 1)
            for total in range(9 * position + 1):
                if loose[total]:
                    for added in range(10):
                        next_loose[total + added] += loose[total]
                if tight[total]:
                    for added in range(digit):
                        next_loose[total + added] += tight[total]
                    next_tight[total + digit] += tight[total]
            loose, tight = next_loose, next_tight
        answer = sum(loose[total] + tight[total] for total in range(1, limit + 1) if good(total))
        answer += sum(value <= bound and not sum_good for value, sum_good in extra)
        return answer
    return count(r) - count(l - 1)


class Solution:
    def countFancy(self, l: int, r: int) -> int:
        return solve(l, r)
