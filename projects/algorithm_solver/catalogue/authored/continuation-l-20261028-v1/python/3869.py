"""Original frontend 3869 variant; qualification unknown."""

def solve(l, r):
    from functools import lru_cache
    def good(value):
        digits = str(value)
        return all(a < b for a, b in zip(digits, digits[1:])) or all(a > b for a, b in zip(digits, digits[1:]))
    monotone = set()
    def extend(value, previous, increasing):
        monotone.add(value)
        for digit in range(previous + 1, 10) if increasing else range(previous):
            extend(value * 10 + digit, digit, increasing)
    for first in range(1, 10):
        extend(first, first, True)
        extend(first, first, False)
    extras = [value for value in monotone if not good(sum(map(int, str(value))))]
    def prefix(limit):
        if limit <= 0:
            return 0
        digits = tuple(map(int, str(limit)))
        @lru_cache(None)
        def count(position, total, tight):
            if position == len(digits):
                return int(good(total))
            bound = digits[position] if tight else 9
            return sum(count(position + 1, total + digit, tight and digit == bound) for digit in range(bound + 1))
        return count(0, 0, True) - 1 + sum(value <= limit for value in extras)
    return prefix(r) - prefix(l - 1)


class Solution:
    def countFancy(self, l, r):
        return solve(l, r)
