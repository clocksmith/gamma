"""3853. Merge Close Characters."""
from __future__ import annotations


def solve(s: str, k: int) -> str:
    """O(n^2 k) time and O(n) space for n<=100; preserve the mandated leftmost-pair merge order."""
    characters = list(s)
    while True:
        removed = False
        for left in range(len(characters)):
            for right in range(left + 1, min(len(characters), left + k + 1)):
                if characters[left] == characters[right]:
                    del characters[right]
                    removed = True
                    break
            if removed:
                break
        if not removed:
            return ''.join(characters)


class Solution:
    def mergeCharacters(self, s: str, k: int) -> str:
        return solve(s, k)
