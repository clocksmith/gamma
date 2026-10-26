"""3827. Count Monobit Integers (Easy).

Specification: https://leetcode.com/problems/count-monobit-integers/description/
"""


def solve(n: int) -> int:
    """O(log(n + 2)) time, O(1) space; include zero and all-ones binary representations."""
    result = 1
    value = 1
    while value <= n:
        result += 1
        value = value * 2 + 1
    return result


class Solution:
    def countMonobit(self, n: int) -> int:
        return solve(n)
