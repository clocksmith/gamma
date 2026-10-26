"""301. Remove Invalid Parentheses: two directional passes removing only surplus parentheses."""


def solve(s: str) -> list[str]:
    """O(n * 2^n) time; O(n^2) stack strings plus output. Inputs are preserved."""
    answers = []

    def visit(text, scan_start, removal_start, opening, closing):
        balance = 0
        for index in range(scan_start, len(text)):
            if text[index] == opening:
                balance += 1
            elif text[index] == closing:
                balance -= 1
            if balance >= 0:
                continue
            for remove in range(removal_start, index + 1):
                if text[remove] == closing and (remove == removal_start or text[remove - 1] != closing):
                    visit(text[:remove] + text[remove + 1:], index, remove, opening, closing)
            return
        reversed_text = text[::-1]
        if opening == '(':
            visit(reversed_text, 0, 0, ')', '(')
        else:
            answers.append(reversed_text)

    visit(s, 0, 0, '(', ')')
    return answers


class Solution:
    def removeInvalidParentheses(self, s: str) -> list[str]:
        return solve(s)
