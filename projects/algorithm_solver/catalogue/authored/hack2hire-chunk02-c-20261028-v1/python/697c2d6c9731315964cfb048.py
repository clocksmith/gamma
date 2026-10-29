"""Hack2Hire 697c2d6c9731315964cfb048 (Accept-Language Header Matching, variant 1) over an INFERRED spec; qualification unknown."""

def solve(header, supported):
    present = set(supported)
    emitted = set()
    result = []
    for raw in header.split(','):
        token = raw.strip(' ')
        matches = [token] if token in present else []
        for tag in matches:
            if tag not in emitted:
                emitted.add(tag)
                result.append(tag)
    return result


class Solution:
    def parseAcceptLanguage(self, header, supported):
        return solve(header, supported)
