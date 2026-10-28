"""567. Permutation in String (Medium).

Specification: https://leetcode.com/problems/permutation-in-string/description/
"""


def solve(s1: str, s2: str) -> bool:
    if len(s1) > len(s2):
        return False
    need = [0] * 26
    window = [0] * 26
    for ch in s1:
        need[ord(ch) - 97] += 1
    for i, ch in enumerate(s2):
        window[ord(ch) - 97] += 1
        if i >= len(s1):
            window[ord(s2[i - len(s1)]) - 97] -= 1
        if window == need:
            return True
    return False


class Solution:
    def checkInclusion(self, s1: str, s2: str) -> bool:
        return solve(s1, s2)
