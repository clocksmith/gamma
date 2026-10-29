"""Hack2Hire 6a987edf0ca9cc4e1c78a9a5 (Final Values by Source Priority) over an INFERRED spec; qualification unknown."""


def solve(sources):
    final = {}
    for row in sources:
        for entry in row:
            cut = entry.index(':')
            final[entry[:cut]] = entry[cut + 1:]
    return [k + ':' + final[k] for k in sorted(final)]


class Solution:
    def finalValues(self, sources):
        return solve(sources)
