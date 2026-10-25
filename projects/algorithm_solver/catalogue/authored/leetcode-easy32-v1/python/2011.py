"""2011. Final Value of Variable After Performing Operations (Easy).

Specification: https://leetcode.com/problems/final-value-of-variable-after-performing-operations/description/
"""


def solve(operations: list[str]) -> int:
    """O(n) time, O(1) space; inspect each operation's middle character."""
    value = 0
    for operation in operations:
        value += 1 if operation[1] == '+' else -1
    return value


class Solution:
    def finalValueAfterOperations(self, operations: list[str]) -> int:
        return solve(operations)
