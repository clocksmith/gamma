"""159. Longest Substring with At Most Two Distinct Characters."""
from collections import defaultdict

def solve(s: str) -> int:
    counts = defaultdict(int)
    left = best = 0
    for right, char in enumerate(s):
        counts[char] += 1
        while len(counts) > 2:
            removed = s[left]
            counts[removed] -= 1
            if counts[removed] == 0:
                del counts[removed]
            left += 1
        best = max(best, right - left + 1)
    return best

class Solution:
    def lengthOfLongestSubstringTwoDistinct(self, s: str) -> int:
        return solve(s)
