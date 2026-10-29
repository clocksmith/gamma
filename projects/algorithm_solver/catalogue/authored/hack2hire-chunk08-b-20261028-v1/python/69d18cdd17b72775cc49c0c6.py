"""Hack2Hire 69d18cdd17b72775cc49c0c6 (Template String Formatter I) over an INFERRED spec; qualification unknown."""

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


def _names(text):
    out, i = [], text.find('{')
    while i >= 0:
        j = text.index('}', i)
        out.append(text[i + 1:j])
        i = text.find('{', j)
    return out


def solve(text, keys, values):
    raw = dict(zip(keys, values))
    expanded = {}
    for root in _names(text):
        if root in expanded:
            continue
        stack = [(root, _names(raw[root]), 0)]
        while stack:
            key, refs, i = stack.pop()
            while i < len(refs) and refs[i] in expanded:
                i += 1
            if i < len(refs):
                stack.append((key, refs, i + 1))
                stack.append((refs[i], _names(raw[refs[i]]), 0))
            elif key not in expanded:
                expanded[key] = _render(raw[key], expanded)
    return _render(text, expanded)


class Solution:
    def formatTemplate(self, text, keys, values):
        return solve(text, keys, values)
