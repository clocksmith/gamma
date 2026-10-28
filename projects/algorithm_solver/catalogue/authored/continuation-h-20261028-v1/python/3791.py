"""Original frontend 3791 development variant; qualification unknown."""

def solve(low, high):
    from functools import lru_cache
    def prefix(limit):
        if limit <= 0:
            return 0
        digits = tuple(map(int, str(limit)))
        @lru_cache(None)
        def count(position, difference, tight):
            if position == len(digits):
                return int(difference == 0)
            bound = digits[position] if tight else 9
            sign = 1 if position % 2 == 0 else -1
            return sum(count(position + 1, difference + sign * digit, tight and digit == bound) for digit in range(bound + 1))
        return count(0, 0, True) - 1
    return prefix(high) - prefix(low - 1)


class Solution:
    def countBalanced(self, low, high):
        return solve(low, high)
