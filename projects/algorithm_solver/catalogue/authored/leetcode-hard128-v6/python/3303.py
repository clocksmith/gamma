"""3303. Find the Occurrence of First Almost Equal Substring.

Forward and reversed Z matches cover every position except at most one; O(n+m) time and space. Lowercase input strings are preserved.
"""

def solve(s: str, pattern: str) -> int:
    def z_values(text):
        z = [0] * len(text)
        left = right = 0
        for index in range(1, len(text)):
            if index <= right:
                z[index] = min(right - index + 1, z[index - left])
            while index + z[index] < len(text) and text[z[index]] == text[index + z[index]]:
                z[index] += 1
            if index + z[index] - 1 > right:
                left, right = index, index + z[index] - 1
        return z

    n, m = len(s), len(pattern)
    if m > n:
        return -1
    forward = z_values(pattern + '#' + s)
    backward = z_values(pattern[::-1] + '#' + s[::-1])
    for start in range(n - m + 1):
        if forward[m + 1 + start] + backward[m + 1 + n - start - m] >= m - 1:
            return start
    return -1


class Solution:
    def minStartingIndex(self, s: str, pattern: str) -> int:
        return solve(s, pattern)
