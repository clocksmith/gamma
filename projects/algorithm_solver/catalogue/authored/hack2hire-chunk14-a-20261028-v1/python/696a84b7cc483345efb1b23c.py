"""Hack2Hire 696a84b7cc483345efb1b23c (Tag Groups Complement Finder) over an INFERRED spec; qualification unknown."""


def solve(groups, filter):
    need = set(filter)
    found = set()
    for group in groups:
        tags = set(group)
        if need <= tags:
            found |= tags
    found -= need
    return sorted(found)


class Solution:
    def complementTags(self, groups, filter):
        return solve(groups, filter)
