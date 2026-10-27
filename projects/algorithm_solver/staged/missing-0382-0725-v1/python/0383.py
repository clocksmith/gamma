"""383. Ransom Note. Count available letters; O(n+m) time."""

from collections import Counter

def solve(ransomNote: str, magazine: str) -> bool:
    counts = Counter(magazine)
    for char in ransomNote:
        if counts[char] == 0:
            return False
        counts[char] -= 1
    return True


class Solution:
    def canConstruct(self, ransomNote: str, magazine: str) -> bool:
        return solve(ransomNote, magazine)
