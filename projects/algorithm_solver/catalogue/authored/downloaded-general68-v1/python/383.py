"""383. Ransom Note (Easy).

Specification: https://leetcode.com/problems/ransom-note/description/
"""


def solve(ransomNote: str, magazine: str) -> bool:
    counts = {}
    for ch in magazine:
        counts[ch] = counts.get(ch, 0) + 1
    for ch in ransomNote:
        if counts.get(ch, 0) == 0:
            return False
        counts[ch] -= 1
    return True


class Solution:
    def canConstruct(self, ransomNote: str, magazine: str) -> bool:
        return solve(ransomNote, magazine)
