"""Hack2Hire 697c2f499731315964cfb056 (Accept-Language Header Matching, variant 2) over an INFERRED spec; qualification unknown."""

def solve(header, supported):
    present = set(supported)
    by_language = {}
    for tag in supported:
        by_language.setdefault(tag[:2], []).append(tag)
    emitted = set()
    result = []
    for raw in header.split(','):
        token = raw.strip(' ')
        if len(token) == 2:
            matches = by_language.get(token, [])
        else:
            matches = [token] if token in present else []
        for tag in matches:
            if tag not in emitted:
                emitted.add(tag)
                result.append(tag)
    return result


class Solution:
    def parseAcceptLanguage(self, header, supported):
        return solve(header, supported)
