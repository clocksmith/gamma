"""340. Longest Substring with At Most K Distinct Characters."""
from collections import defaultdict

def solve(s: str, k: int) -> int:
    counts = defaultdict(int)
    left = best = 0
    for right, char in enumerate(s):
        counts[char] += 1
        while len(counts) > k:
            removed = s[left]
            counts[removed] -= 1
            if counts[removed] == 0:
                del counts[removed]
            left += 1
        best = max(best, right - left + 1)
    return best

class Solution:
    def lengthOfLongestSubstringKDistinct(self, s: str, k: int) -> int:
        return solve(s, k)
