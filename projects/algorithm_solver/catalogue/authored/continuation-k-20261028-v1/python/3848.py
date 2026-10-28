from math import factorial


def solve(n):
    text = str(n)
    total = sum(factorial(int(c)) for c in text)
    return sorted(str(total)) == sorted(text)


class Solution:
    def isDigitorialPermutation(self, n):
        return solve(n)
