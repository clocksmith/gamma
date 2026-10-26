"""2982. Find Longest Special Substring That Occurs Thrice II: retain each character's three longest runs and account for overlapping occurrences."""


def solve(s: str) -> int:
    """O(n) time and O(1) auxiliary space for the lowercase alphabet; inputs are read-only."""
    longest = [[0, 0, 0] for _ in range(26)]
    left = 0
    while left < len(s):
        right = left + 1
        while right < len(s) and s[right] == s[left]:
            right += 1
        runs = longest[ord(s[left]) - ord('a')]
        length = right - left
        if length >= runs[0]:
            runs[:] = [length, runs[0], runs[1]]
        elif length >= runs[1]:
            runs[1:] = [length, runs[1]]
        elif length > runs[2]:
            runs[2] = length
        left = right
    best = 0
    for first, second, third in longest:
        best = max(best, first - 2, min(first - 1, second), third)
    return best if best > 0 else -1


class Solution:
    def maximumLength(self, s: str) -> int:
        return solve(s)
