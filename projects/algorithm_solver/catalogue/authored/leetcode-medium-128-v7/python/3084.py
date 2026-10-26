"""3084. Count Substrings Starting and Ending with Given Character: count ordered endpoint choices among occurrences of the required character."""


def solve(s: str, c: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    occurrences = s.count(c)
    return occurrences * (occurrences + 1) // 2


class Solution:
    def countSubstrings(self, s: str, c: str) -> int:
        return solve(s, c)
