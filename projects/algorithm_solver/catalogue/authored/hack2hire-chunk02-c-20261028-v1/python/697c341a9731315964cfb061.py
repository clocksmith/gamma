"""Hack2Hire 697c341a9731315964cfb061 (Accept-Language Header Matching, variant 4) over an INFERRED spec; qualification unknown."""

def _thousandths(text):
    whole, _, fraction = text.partition('.')
    return int(whole) * 1000 + int((fraction + '000')[:3])


def solve(header, supported):
    exact, language, star = {}, {}, None  # first occurrence: (quality, position)
    for position, raw in enumerate(header.split(',')):
        token, _, parameter = raw.strip(' ').partition(';')
        quality = _thousandths(parameter[2:]) if parameter else 1000
        if token == '*':
            if star is None:
                star = (quality, position)
        elif len(token) == 2:
            language.setdefault(token, (quality, position))
        else:
            exact.setdefault(token, (quality, position))
    ranked = []
    for index, tag in enumerate(supported):
        found = [entry for entry in (exact.get(tag), language.get(tag[:2]), star) if entry is not None]
        if not found or found[0][0] == 0:
            continue
        ranked.append((-found[0][0], min(entry[1] for entry in found), index, tag))
    ranked.sort()
    return [entry[3] for entry in ranked]


class Solution:
    def parseAcceptLanguage(self, header, supported):
        return solve(header, supported)
