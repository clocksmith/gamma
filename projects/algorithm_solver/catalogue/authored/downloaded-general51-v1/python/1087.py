"""1087. Brace Expansion (Medium).

Specification: https://leetcode.com/problems/brace-expansion/description/
"""


def solve(s: str) -> list[str]:
    groups = []
    index = 0
    while index < len(s):
        if s[index] == '{':
            end = s.index('}', index)
            groups.append(sorted(s[index + 1:end].split(',')))
            index = end + 1
        else:
            groups.append([s[index]])
            index += 1
    result = ['']
    for group in groups:
        nxt = []
        for prefix in result:
            for ch in group:
                nxt.append(prefix + ch)
        result = nxt
    return sorted(result)


class Solution:
    def expand(self, s: str) -> list[str]:
        return solve(s)
