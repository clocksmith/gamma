"""Hack2Hire 68bad975b5314dcd938cb9ff (Top 10 Words, variant 2 of 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

import re

_WORD = re.compile('[A-Za-z]+')


class WordFrequencyTracker:
    def __init__(self):
        self.counts = {}
        self.top = []

    def _better(self, a, b):
        ca, cb = self.counts[a], self.counts[b]
        return ca > cb or (ca == cb and a < b)

    def addText(self, text):
        for match in _WORD.findall(text):
            word = match.lower()
            self.counts[word] = self.counts.get(word, 0) + 1
            top = self.top
            if word in top:
                top.remove(word)
            elif len(top) == 10 and not self._better(word, top[-1]):
                continue
            i = len(top)
            while i > 0 and self._better(word, top[i - 1]):
                i -= 1
            top.insert(i, word)
            if len(top) > 10:
                top.pop()

    def getTop10(self):
        return [[word, self.counts[word]] for word in self.top]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'WordFrequencyTracker' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = WordFrequencyTracker(*argument_lists[0])
    allowed = {'addText', 'getTop10'}
    voids = {'addText'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
