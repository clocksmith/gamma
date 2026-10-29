"""Hack2Hire 6a9748740ca9cc4e1c789f00 (Autocorrect Prototype) over an INFERRED spec; qualification unknown."""


def solve(words, queries):
    groups = {}
    for w in words:
        groups.setdefault(''.join(sorted(w)), []).append(w)
    return [list(groups.get(''.join(sorted(q)), ())) for q in queries]


class Solution:
    def findAnagrams(self, words, queries):
        return solve(words, queries)
