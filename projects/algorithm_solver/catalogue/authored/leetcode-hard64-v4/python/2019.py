"""2019. The Score of Students Solving Math Expression."""


def solve(s: str, answers: list[int]) -> int:
    """Precedence evaluation plus bounded parenthesization DP; O(m^3*U^2+A) time, O(m^2*U) space, U=1002. Inputs are preserved."""
    digits = [int(s[index]) for index in range(0, len(s), 2)]
    operators = s[1::2]
    correct = 0
    product = digits[0]
    for operator, value in zip(operators, digits[1:]):
        if operator == '*':
            product *= value
        else:
            correct += product
            product = value
    correct += product
    size = len(digits)
    possible = [[set() for _ in range(size)] for _ in range(size)]
    for index, value in enumerate(digits):
        possible[index][index].add(value)
    for width in range(2, size + 1):
        for left in range(size - width + 1):
            right = left + width - 1
            outcomes = possible[left][right]
            for split in range(left, right):
                for first in possible[left][split]:
                    for second in possible[split + 1][right]:
                        value = first + second if operators[split] == '+' else first * second
                        # Keep an overflow sentinel: a later multiplication by zero can still yield zero.
                        outcomes.add(min(value, 1001))
    alternatives = possible[0][-1]
    return sum(5 if value == correct else 2 if value in alternatives else 0 for value in answers)


class Solution:
    def scoreOfStudents(self, s: str, answers: list[int]) -> int:
        return solve(s, answers)
