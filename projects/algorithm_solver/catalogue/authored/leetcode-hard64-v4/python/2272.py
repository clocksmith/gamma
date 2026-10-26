"""2272. Substring With Largest Variance."""

from collections import Counter


def solve(s: str) -> int:
    """Ordered-letter Kadane scans retaining a required minority; O(A^2*n) time and O(A) space. Inputs are preserved."""
    frequency = Counter(s)
    answer = 0
    for major in frequency:
        for minor in frequency:
            if major == minor:
                continue
            remaining_minor = frequency[minor]
            difference = 0
            has_minor = False
            for character in s:
                if character == major:
                    difference += 1
                elif character == minor:
                    difference -= 1
                    remaining_minor -= 1
                    has_minor = True
                else:
                    continue
                if has_minor:
                    answer = max(answer, difference)
                if difference < 0 and remaining_minor > 0:
                    difference = 0
                    has_minor = False
    return answer


class Solution:
    def largestVariance(self, s: str) -> int:
        return solve(s)
