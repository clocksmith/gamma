"""424. Longest Repeating Character Replacement. Sliding window with a nondecreasing maximum frequency bound."""

from collections import Counter

def solve(s: str, k: int) -> int:
    counts = Counter()
    left = maximum = answer = 0
    for right, char in enumerate(s):
        counts[char] += 1
        maximum = max(maximum, counts[char])
        while right - left + 1 - maximum > k:
            counts[s[left]] -= 1
            left += 1
        answer = max(answer, right - left + 1)
    return answer


class Solution:
    def characterReplacement(self, s: str, k: int) -> int:
        return solve(s, k)
