"""2516. Take K of Each Character From Left and Right: retain the longest middle window leaving at least k of each character outside."""


def solve(s: str, k: int) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    remaining = [0, 0, 0]
    for character in s:
        remaining[ord(character) - ord('a')] += 1
    if min(remaining) < k:
        return -1
    left = best = 0
    for right, character in enumerate(s):
        code = ord(character) - ord('a')
        remaining[code] -= 1
        while remaining[code] < k:
            remaining[ord(s[left]) - ord('a')] += 1
            left += 1
        best = max(best, right - left + 1)
    return len(s) - best


class Solution:
    def takeCharacters(self, s: str, k: int) -> int:
        return solve(s, k)
