"""76. Minimum Window Substring (Hard).

Specification: https://leetcode.com/problems/minimum-window-substring/description/
"""


def solve(s: str, t: str) -> str:
    if not t:
        return ''
    need = {}
    for ch in t:
        need[ch] = need.get(ch, 0) + 1
    required = len(need)
    formed = 0
    window = {}
    left = 0
    best = (float('inf'), 0, 0)
    for right, ch in enumerate(s):
        window[ch] = window.get(ch, 0) + 1
        if ch in need and window[ch] == need[ch]:
            formed += 1
        while formed == required:
            if right - left + 1 < best[0]:
                best = (right - left + 1, left, right)
            left_ch = s[left]
            window[left_ch] -= 1
            if left_ch in need and window[left_ch] < need[left_ch]:
                formed -= 1
            left += 1
    return '' if best[0] == float('inf') else s[best[1]:best[2] + 1]


class Solution:
    def minWindow(self, s: str, t: str) -> str:
        return solve(s, t)
