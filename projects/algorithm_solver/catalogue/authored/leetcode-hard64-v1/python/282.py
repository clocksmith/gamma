"""282. Expression Add Operators: backtracking with the last multiplicative term."""


def solve(num: str, target: int) -> list[str]:
    """O(n * 4^n) time; O(n^2) stack strings plus output. Inputs are preserved."""
    answers = []

    def visit(start, total, last, expression):
        if start == len(num):
            if total == target:
                answers.append(expression)
            return
        value = 0
        for end in range(start, len(num)):
            if end > start and num[start] == '0':
                break
            value = value * 10 + ord(num[end]) - ord('0')
            token = num[start:end + 1]
            if start == 0:
                visit(end + 1, value, value, token)
            else:
                visit(end + 1, total + value, value, expression + '+' + token)
                visit(end + 1, total - value, -value, expression + '-' + token)
                product = last * value
                visit(end + 1, total - last + product, product, expression + '*' + token)

    visit(0, 0, 0, '')
    return answers


class Solution:
    def addOperators(self, num: str, target: int) -> list[str]:
        return solve(num, target)
