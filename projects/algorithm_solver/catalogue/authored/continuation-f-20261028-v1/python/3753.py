"""Original frontend 3753 development candidate; qualification unknown."""

def solve(num1, num2):
    from functools import lru_cache
    def prefix(limit):
        if limit <= 0:
            return 0
        digits = tuple(map(int, str(limit)))
        @lru_cache(None)
        def visit(position, older, previous, tight):
            if position == len(digits):
                return 1, 0
            count = total = 0
            bound = digits[position] if tight else 9
            for digit in range(bound + 1):
                next_tight = tight and digit == bound
                if previous == -1 and digit == 0:
                    children, subtotal = visit(position + 1, -1, -1, next_tight)
                    bonus = 0
                else:
                    bonus = int(older != -1 and ((previous > older and previous > digit) or (previous < older and previous < digit)))
                    children, subtotal = visit(position + 1, previous, digit, next_tight)
                count += children
                total += subtotal + children * bonus
            return count, total
        return visit(0, -1, -1, True)[1]
    return prefix(num2) - prefix(num1 - 1)


class Solution:
    def totalWaviness(self, num1, num2):
        return solve(num1, num2)
