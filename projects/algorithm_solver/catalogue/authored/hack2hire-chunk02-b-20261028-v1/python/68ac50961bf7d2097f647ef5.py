"""Original Hack2Hire 68ac50961bf7d2097f647ef5 variant over an INFERRED specification; qualification unknown."""


def solve(words):
    ordered = sorted(words)
    prefixes = {ordered[i] for i in range(len(ordered) - 1) if ordered[i + 1].startswith(ordered[i])}
    return [word for word in words if word not in prefixes]


class Solution:
    def removePrefixStrings(self, words):
        return solve(words)
