"""Original frontend 3747 development candidate; qualification unknown."""

def solve(n):
    digits = str(n)
    answer = sum(9 ** length for length in range(1, len(digits)))
    for index, char in enumerate(digits):
        digit = int(char)
        answer += max(0, digit - 1) * 9 ** (len(digits) - index - 1)
        if digit == 0:
            return answer
    return answer + 1


class Solution:
    def countDistinct(self, n):
        return solve(n)
