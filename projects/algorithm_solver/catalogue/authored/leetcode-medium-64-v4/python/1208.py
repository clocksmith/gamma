"""1208. Get Equal Substrings Within Budget: maintain the longest affordable sliding window."""


def solve(s: str, t: str, maxCost: int) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    left = total = best = 0
    for right in range(len(s)):
        total += abs(ord(s[right]) - ord(t[right]))
        while total > maxCost:
            total -= abs(ord(s[left]) - ord(t[left]))
            left += 1
        best = max(best, right - left + 1)
    return best


class Solution:
    def equalSubstring(self, s: str, t: str, maxCost: int) -> int:
        return solve(s, t, maxCost)
