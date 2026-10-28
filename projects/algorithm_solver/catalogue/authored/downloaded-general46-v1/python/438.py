"""438. Find All Anagrams in a String (Medium).

Specification: https://leetcode.com/problems/find-all-anagrams-in-a-string/description/
"""


def solve(s: str, p: str) -> list[int]:
    result = []
    if len(p) > len(s):
        return result
    need = [0] * 26
    window = [0] * 26
    for ch in p:
        need[ord(ch) - 97] += 1
    for i, ch in enumerate(s):
        window[ord(ch) - 97] += 1
        if i >= len(p):
            window[ord(s[i - len(p)]) - 97] -= 1
        if i >= len(p) - 1 and window == need:
            result.append(i - len(p) + 1)
    return result


class Solution:
    def findAnagrams(self, s: str, p: str) -> list[int]:
        return solve(s, p)
