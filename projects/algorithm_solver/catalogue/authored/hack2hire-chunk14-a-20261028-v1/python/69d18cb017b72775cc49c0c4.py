"""Hack2Hire 69d18cb017b72775cc49c0c4 (Template String Formatter II) over an INFERRED spec; qualification unknown."""


_HEAD = ', plural, one{'
_MID = '} other{'


def solve(text, keys, values):
    lookup = dict(zip(keys, values))
    out = []
    i, length = 0, len(text)
    while i < length:
        if text[i] != '{':
            j = text.find('{', i)
            if j < 0:
                j = length
            out.append(text[i:j])
            i = j
            continue
        j = i + 1
        while text[j] != '}' and text[j] != ',':
            j += 1
        name = text[i + 1:j]
        if text[j] == '}':
            out.append(lookup[name] if name in lookup else text[i:j + 1])
            i = j + 1
            continue
        one_start = j + len(_HEAD)
        one_end = text.index('}', one_start)
        other_start = one_end + len(_MID)
        other_end = text.index('}', other_start)
        end = other_end + 2
        if name in lookup:
            value = lookup[name]
            branch = text[one_start:one_end] if value == '1' else text[other_start:other_end]
            out.append(branch.replace('#', value))
        else:
            out.append(text[i:end])
        i = end
    return ''.join(out)


class Solution:
    def formatTemplate(self, text, keys, values):
        return solve(text, keys, values)
