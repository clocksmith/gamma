"""Hack2Hire 69d18c8717b72775cc49c0c2 (Template String Formatter I) over an INFERRED spec; qualification unknown."""

def _render(text, lookup):
    out = []
    i, n = 0, len(text)
    while i < n:
        if text[i] == '{':
            j = text.index('}', i)
            out.append(lookup[text[i + 1:j]])
            i = j + 1
        else:
            j = text.find('{', i)
            if j < 0:
                j = n
            out.append(text[i:j])
            i = j
    return ''.join(out)


def solve(text, keys, values):
    return _render(text, dict(zip(keys, values)))


class Solution:
    def formatTemplate(self, text, keys, values):
        return solve(text, keys, values)
