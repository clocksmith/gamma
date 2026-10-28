"""Original frontend 3751 development candidate; qualification unknown."""

def solve(num1, num2):
    answer = 0
    for value in range(num1, num2 + 1):
        digits = str(value)
        for i in range(1, len(digits) - 1):
            answer += (digits[i] > digits[i - 1] and digits[i] > digits[i + 1]) or (digits[i] < digits[i - 1] and digits[i] < digits[i + 1])
    return answer


class Solution:
    def totalWaviness(self, num1, num2):
        return solve(num1, num2)
