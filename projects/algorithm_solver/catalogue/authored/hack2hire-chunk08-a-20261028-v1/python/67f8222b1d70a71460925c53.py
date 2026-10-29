"""Hack2Hire 67f8222b1d70a71460925c53 (Prefix Search II) over an INFERRED spec; qualification unknown."""


def solve(bizNames, searchWord):
    depth = len(searchWord)
    root = {}
    for index, name in enumerate(bizNames):
        for position, word in enumerate(name.split(' ')):
            node = root
            for ch in word[:depth].lower():
                child = node.get(ch)
                if child is None:
                    child = node[ch] = {'#': []}
                child['#'].append((index, position))
                node = child
    out = []
    node = root
    for ch in searchWord.lower():
        node = node.get(ch) if node is not None else None
        if node is None:
            out.append([])
            continue
        first = {}
        for index, position in node['#']:
            if index not in first or position < first[index]:
                first[index] = position
        out.append([bizNames[i] for _, _, i in sorted((p, bizNames[i], i) for i, p in first.items())])
    return out


class Solution:
    def searchSuggestions(self, bizNames, searchWord):
        return solve(bizNames, searchWord)
