"""1790. Check if One String Swap Can Make Strings Equal (Easy).

Specification: https://leetcode.com/problems/check-if-one-string-swap-can-make-strings-equal/description/
"""


def solve(s1: str, s2: str) -> bool:
    """O(n) time, O(1) space; zero mismatches or one crossed pair permits at most one swap."""
    first_mismatch = -1
    second_mismatch = -1
    for index in range(len(s1)):
        if s1[index] == s2[index]:
            continue
        if first_mismatch == -1:
            first_mismatch = index
        elif second_mismatch == -1:
            second_mismatch = index
        else:
            return False
    if first_mismatch == -1:
        return True
    if second_mismatch == -1:
        return False
    return s1[first_mismatch] == s2[second_mismatch] and s1[second_mismatch] == s2[first_mismatch]


class Solution:
    def areAlmostEqual(self, s1: str, s2: str) -> bool:
        return solve(s1, s2)
