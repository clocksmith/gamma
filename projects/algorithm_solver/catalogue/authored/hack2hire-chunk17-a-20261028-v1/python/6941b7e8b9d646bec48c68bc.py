"""Hack2Hire 6941b7e8b9d646bec48c68bc (String Tokenization) over an INFERRED spec; qualification unknown."""


def solve(text, dictionary):
    root = [{}, None]  # [children, id ending here]
    for entry in dictionary:
        key, ident = entry.split(':')
        node = root
        for ch in key:
            child = node[0].get(ch)
            if child is None:
                child = [{}, None]
                node[0][ch] = child
            node = child
        node[1] = ident
    out = []
    i = 0
    n = len(text)
    while i < n:
        node = root
        j = i
        best = None
        best_end = i
        while j < n:
            node = node[0].get(text[j])
            if node is None:
                break
            j += 1
            if node[1] is not None:
                best = node[1]
                best_end = j
        if best is None:
            out.append(text[i])
            i += 1
        else:
            out.append(best)
            i = best_end
    return out


class Solution:
    def tokenize(self, text, dictionary):
        return solve(text, dictionary)
