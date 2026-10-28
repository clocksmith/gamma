"""1156. Swap For Longest Repeated Character Substring (Medium).

Specification: https://leetcode.com/problems/swap-for-longest-repeated-character-substring/description/
"""


def solve(text: str) -> int:
    groups = []
    i = 0
    while i < len(text):
        j = i
        while j < len(text) and text[j] == text[i]:
            j += 1
        groups.append((text[i], j - i))
        i = j
    total = {}
    for ch, count in groups:
        total[ch] = total.get(ch, 0) + count
    best = 0
    for ch, count in groups:
        best = max(best, count + 1 if total[ch] > count else count)
    for i in range(len(groups) - 2):
        if groups[i][0] == groups[i + 2][0] and groups[i + 1][1] == 1:
            merged = groups[i][1] + groups[i + 2][1]
            best = max(best, merged + 1 if total[groups[i][0]] > merged else merged)
    return best


class Solution:
    def maxRepOpt1(self, text: str) -> int:
        return solve(text)
