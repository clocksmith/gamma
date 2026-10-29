"""Hack2Hire 695c711d68e2c0dd046c4955 (Most Frequent Substring) over an INFERRED spec; qualification unknown."""

def solve(str, n):
    text = str
    if n > len(text):
        return ''
    counts = {}
    for i in range(len(text) - n + 1):
        window = text[i:i + n]
        counts[window] = counts.get(window, 0) + 1
    best, best_count = '', 0
    for window, c in counts.items():
        if c > best_count or (c == best_count and window < best):
            best, best_count = window, c
    return best


class Solution:
    def mostFrequentSubstring(self, str, n):
        return solve(str, n)
