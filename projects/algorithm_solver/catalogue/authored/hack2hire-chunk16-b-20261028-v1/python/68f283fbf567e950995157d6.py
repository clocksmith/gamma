"""Hack2Hire 68f283fbf567e950995157d6 (Pig Latin Sentence Converter) over an INFERRED spec; qualification unknown."""


def solve(sentence):
    if sentence == '':
        return ''
    out = []
    for word in sentence.split(' '):
        if word[0] in 'aeiouAEIOU':
            out.append(word + 'way')
        else:
            out.append(word[1:] + word[0] + 'ay')
    return ' '.join(out)


class Solution:
    def toPigLatin(self, sentence):
        return solve(sentence)
