"""1023. Camelcase Matching (Medium).

Specification: https://leetcode.com/problems/camelcase-matching/description/
"""


def _matches(query, pattern):
    index = 0
    for ch in query:
        if index < len(pattern) and ch == pattern[index]:
            index += 1
        elif ch.isupper():
            return False
    return index == len(pattern)


def solve(queries: list[str], pattern: str) -> list[bool]:
    return [_matches(query, pattern) for query in queries]


class Solution:
    def camelMatch(self, queries: list[str], pattern: str) -> list[bool]:
        return solve(queries, pattern)
