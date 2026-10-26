"""2839. Check if Strings Can be Made Equal With Operations I (Easy).

Specification: https://leetcode.com/problems/check-if-strings-can-be-made-equal-with-operations-i/description/
"""


def solve(s1: str, s2: str) -> bool:
    """O(1) time and space for strings of length four; preserve both strings."""
    for offset in range(2):
        unchanged = s1[offset] == s2[offset] and s1[offset + 2] == s2[offset + 2]
        swapped = s1[offset] == s2[offset + 2] and s1[offset + 2] == s2[offset]
        if not unchanged and not swapped:
            return False
    return True


class Solution:
    def canBeEqual(self, s1: str, s2: str) -> bool:
        return solve(s1, s2)
