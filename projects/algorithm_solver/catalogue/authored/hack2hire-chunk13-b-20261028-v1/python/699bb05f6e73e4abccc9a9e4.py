"""Hack2Hire 699bb05f6e73e4abccc9a9e4 (Sentence Variations with Anagram) over an INFERRED spec; qualification unknown."""


def solve(wordSet, sentences):
    groups = {}
    for word in wordSet:
        groups.setdefault(''.join(sorted(word)), []).append(word)
    for group in groups.values():
        group.sort()
    options = {}

    def choices(word):
        if word not in options:
            group = groups.get(''.join(sorted(word)), [])
            options[word] = group if word in group else sorted(group + [word])
        return options[word]

    out = []
    for sentence in sentences:
        partial = None
        for word in sentence.split(' '):
            opts = choices(word)
            partial = list(opts) if partial is None else [p + ' ' + o for p in partial for o in opts]
        out.append(partial)
    return out


class Solution:
    def sentenceVariations(self, wordSet, sentences):
        return solve(wordSet, sentences)
