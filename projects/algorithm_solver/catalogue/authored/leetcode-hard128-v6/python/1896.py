"""1896. Minimum Cost to Change the Final Value of Expression.

Iterative expression reduction with costs for both Boolean outcomes; O(n) time and space. AND and OR have equal precedence.
"""

def solve(expression: str) -> int:
    values, operators = [], []

    def apply():
        operator = operators.pop()
        right, left = values.pop(), values.pop()
        cost = [float('inf'), float('inf')]
        for first in (0, 1):
            for second in (0, 1):
                for chosen in ('&', '|'):
                    result = first & second if chosen == '&' else first | second
                    cost[result] = min(cost[result], left[first] + right[second] + (chosen != operator))
        values.append(cost)

    for char in expression:
        if char in '01':
            values.append([int(char), 1 - int(char)])
        elif char == '(':
            operators.append(char)
        elif char == ')':
            while operators[-1] != '(':
                apply()
            operators.pop()
        else:
            while operators and operators[-1] != '(':
                apply()
            operators.append(char)
    while operators:
        apply()
    return max(values[0])


class Solution:
    def minOperationsToFlip(self, expression: str) -> int:
        return solve(expression)
