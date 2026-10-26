"""2167. Minimum Time to Remove All Cars Containing Illegal Goods."""


def solve(s: str) -> int:
    """Optimal prefix removals plus a suffix cut; O(n) time and O(1) space. Inputs are preserved."""
    prefix = 0
    answer = len(s)
    for index, character in enumerate(s):
        if character == '1':
            prefix = min(prefix + 2, index + 1)
        answer = min(answer, prefix + len(s) - index - 1)
    return answer


class Solution:
    def minimumTime(self, s: str) -> int:
        return solve(s)
