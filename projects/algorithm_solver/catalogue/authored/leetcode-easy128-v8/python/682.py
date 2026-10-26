"""682. Baseball Game (Easy).

Specification: https://leetcode.com/problems/baseball-game/description/
"""


def solve(operations: list[str]) -> int:
    """O(n) time and space; maintain the valid score stack under the valid-operation contract."""
    scores = []
    for operation in operations:
        if operation == 'C':
            scores.pop()
        elif operation == 'D':
            scores.append(2 * scores[-1])
        elif operation == '+':
            scores.append(scores[-1] + scores[-2])
        else:
            scores.append(int(operation))
    return sum(scores)


class Solution:
    def calPoints(self, operations: list[str]) -> int:
        return solve(operations)
