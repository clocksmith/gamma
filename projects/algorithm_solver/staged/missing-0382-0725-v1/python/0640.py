"""640. Solve the Equation."""

import re

def solve(equation: str) -> str:
    def parse(text):
        coefficient = constant = 0
        for term in re.findall(r'[+-]?[^+-]+', text):
            if term.endswith('x'):
                factor = term[:-1]
                coefficient += -1 if factor == '-' else 1 if factor in ('', '+') else int(factor)
            else:
                constant += int(term)
        return coefficient, constant
    left, right = equation.split('=')
    a, b = parse(left)
    c, d = parse(right)
    coefficient, value = a - c, d - b
    if coefficient == 0:
        return 'Infinite solutions' if value == 0 else 'No solution'
    return 'x=' + str(value // coefficient)


class Solution:
    def solveEquation(self, equation: str) -> str:
        return solve(equation)
