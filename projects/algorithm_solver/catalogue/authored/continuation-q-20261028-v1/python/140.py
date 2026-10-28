"""Original frontend 140 source-defined native ABI; qualification unknown."""

def solve(s, wordDict):
    dictionary = set(wordDict)
    suffixes = [[] for _ in range(len(s) + 1)]
    suffixes[-1] = ['']
    for start in range(len(s) - 1, -1, -1):
        for end in range(start + 1, min(len(s), start + 10) + 1):
            word = s[start:end]
            if word in dictionary:
                suffixes[start].extend(word + (' ' + tail if tail else '') for tail in suffixes[end])
    return suffixes[0]


class Solution:
    def wordBreak(self, s, wordDict):
        return solve(s, wordDict)
