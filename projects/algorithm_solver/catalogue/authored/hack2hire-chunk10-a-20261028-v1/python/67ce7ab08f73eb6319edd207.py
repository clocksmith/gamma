"""Hack2Hire 67ce7ab08f73eb6319edd207 (Custom String Sorting) over an INFERRED spec; qualification unknown."""


def solve(customOrder, words):
    # rank characters: the i-th letter of customOrder becomes chr(97 + i), so plain string order is the custom order
    table = str.maketrans(customOrder, ''.join(chr(97 + i) for i in range(len(customOrder))))
    keys = [w.translate(table) for w in words]
    order = sorted(range(len(words)), key=keys.__getitem__)
    return [words[i] for i in order]


class Solution:
    def customSort(self, customOrder, words):
        return solve(customOrder, words)
