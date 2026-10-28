"""640. Solve the Equation (Medium).

Specification: https://leetcode.com/problems/solve-the-equation/description/
"""


def _parse_side(text):
    coefficient = 0
    constant = 0
    sign = 1
    i = 0
    while i < len(text):
        if text[i] == '+':
            sign = 1
            i += 1
            continue
        if text[i] == '-':
            sign = -1
            i += 1
            continue
        number_text = ''
        while i < len(text) and text[i].isdigit():
            number_text += text[i]
            i += 1
        if i < len(text) and text[i] == 'x':
            coefficient += sign * (1 if number_text == '' else int(number_text))
            i += 1
        else:
            constant += sign * int(number_text)
    return coefficient, constant


def solve(equation: str) -> str:
    left_text, right_text = equation.split('=')
    left = _parse_side(left_text)
    right = _parse_side(right_text)
    coefficient = left[0] - right[0]
    constant = right[1] - left[1]
    if coefficient == 0:
        return 'Infinite solutions' if constant == 0 else 'No solution'
    return f"x={int(constant / coefficient)}"


class Solution:
    def solveEquation(self, equation: str) -> str:
        return solve(equation)
