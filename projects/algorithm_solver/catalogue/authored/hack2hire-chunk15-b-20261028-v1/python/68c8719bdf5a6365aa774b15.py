"""Hack2Hire 68c8719bdf5a6365aa774b15 (Find Anagram in String) over an INFERRED spec; qualification unknown."""


POW = [51 ** (i % 7) for i in range(26)]


def signature(word):
    parts = [0, 0, 0, 0]
    for c in word:
        i = ord(c) - 97
        parts[i // 7] += POW[i]
    return (parts[0], parts[1], parts[2], parts[3])


def solve(words, s):
    by_length = {}
    for index, w in enumerate(words):
        by_length.setdefault(len(w), {}).setdefault(signature(w), []).append(index)
    best = -1
    codes = [ord(c) - 97 for c in s]
    for length, table in by_length.items():
        if length > len(codes):
            continue
        parts = [0, 0, 0, 0]
        for i in range(length):
            c = codes[i]
            parts[c // 7] += POW[c]
        i = length
        while True:
            hit = table.get((parts[0], parts[1], parts[2], parts[3]))
            if hit is not None:
                for index in hit:
                    if best < 0 or index < best:
                        best = index
                del table[(parts[0], parts[1], parts[2], parts[3])]
                if not table:
                    break
            if i == len(codes):
                break
            c = codes[i]
            parts[c // 7] += POW[c]
            c = codes[i - length]
            parts[c // 7] -= POW[c]
            i += 1
    return '' if best < 0 else words[best]


class Solution:
    def firstAnagramWord(self, words, s):
        return solve(words, s)
