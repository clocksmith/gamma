"""43. Multiply Strings (Medium).

Specification: https://leetcode.com/problems/multiply-strings/description/
"""


def solve(num1: str, num2: str) -> str:
    if num1 == '0' or num2 == '0':
        return '0'
    result = [0] * (len(num1) + len(num2))
    for i in range(len(num1) - 1, -1, -1):
        for j in range(len(num2) - 1, -1, -1):
            product = int(num1[i]) * int(num2[j]) + result[i + j + 1]
            result[i + j + 1] = product % 10
            result[i + j] += product // 10
    text = "".join(str(v) for v in result)
    while text[0] == '0':
        text = text[1:]
    return text


class Solution:
    def multiply(self, num1: str, num2: str) -> str:
        return solve(num1, num2)
