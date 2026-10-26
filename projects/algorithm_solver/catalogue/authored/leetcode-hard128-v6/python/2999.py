"""2999. Count the Number of Powerful Integers.

Remove the fixed suffix and count bounded prefixes by digit DP; O(log finish + len(s)) time and space. Inputs are preserved.
"""

def solve(start: int, finish: int, limit: int, s: str) -> int:
    if any(int(char) > limit for char in s):
        return 0
    suffix = int(s)
    base = 10 ** len(s)

    def count(bound):
        if bound < suffix:
            return 0
        maximum = (bound - suffix) // base
        less, equal = 0, 1
        for char in str(maximum):
            digit = int(char)
            less = less * (limit + 1) + equal * min(digit, limit + 1)
            equal = equal if digit <= limit else 0
        result = less + equal
        if s[0] == '0':
            result -= 1
        return result

    return count(finish) - count(start - 1)


class Solution:
    def numberOfPowerfulInt(self, start: int, finish: int, limit: int, s: str) -> int:
        return solve(start, finish, limit, s)
