"""Original frontend 745 variant; qualification unknown."""


class WordFilter:
    def __init__(self, words):
        self.latest = {}
        for position, word in enumerate(words):
            for p in range(1, len(word) + 1):
                prefix = word[:p] + '#'
                for s in range(len(word)):
                    self.latest[prefix + word[s:]] = position

    def f(self, pref, suff):
        return self.latest.get(pref + '#' + suff, -1)
