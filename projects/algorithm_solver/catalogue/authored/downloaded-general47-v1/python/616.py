"""616. Add Bold Tag in String (Medium).

Specification: https://leetcode.com/problems/add-bold-tag-in-string/description/
"""


def solve(s: str, words: list[str]) -> str:
    bold = [False] * len(s)
    for word in words:
        start = s.find(word)
        while start != -1:
            for i in range(start, start + len(word)):
                bold[i] = True
            start = s.find(word, start + 1)
    result = ''
    for i, ch in enumerate(s):
        if bold[i] and (i == 0 or not bold[i - 1]):
            result += '<b>'
        result += ch
        if bold[i] and (i + 1 == len(s) or not bold[i + 1]):
            result += '</b>'
    return result


class Solution:
    def addBoldTag(self, s: str, words: list[str]) -> str:
        return solve(s, words)
