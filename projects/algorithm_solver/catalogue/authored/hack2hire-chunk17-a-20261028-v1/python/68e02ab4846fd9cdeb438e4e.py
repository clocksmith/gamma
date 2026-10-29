"""Hack2Hire 68e02ab4846fd9cdeb438e4e (URL Query Parameter Parsing) over an INFERRED spec; qualification unknown."""


def solve(url):
    mark = url.find('?')
    if mark < 0:
        return {}
    values = {}
    for piece in url[mark + 1:].split('&'):
        if not piece:
            continue
        eq = piece.find('=')
        key, value = (piece, '') if eq < 0 else (piece[:eq], piece[eq + 1:])
        if not key:
            continue
        current = values.get(key)
        if current is None:
            values[key] = value
        elif type(current) is list:
            current.append(value)
        else:
            values[key] = [current, value]
    return values


class Solution:
    def parseQuery(self, url):
        return solve(url)
