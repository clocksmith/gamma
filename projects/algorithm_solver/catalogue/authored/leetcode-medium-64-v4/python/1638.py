"""1638. Count Substrings That Differ by One Character: extend equal and one-mismatch suffix counts along matching diagonals."""


def solve(s: str, t: str) -> int:
    """O(n * m) time and O(m) auxiliary space; inputs are read-only."""
    equal = [0] * (len(t) + 1)
    different = [0] * (len(t) + 1)
    total = 0
    for first in s:
        previous_equal = previous_different = 0
        for index, second in enumerate(t, 1):
            old_equal, old_different = equal[index], different[index]
            if first == second:
                equal[index] = previous_equal + 1
                different[index] = previous_different
            else:
                equal[index] = 0
                different[index] = previous_equal + 1
            total += different[index]
            previous_equal, previous_different = old_equal, old_different
    return total


class Solution:
    def countSubstrings(self, s: str, t: str) -> int:
        return solve(s, t)
