"""Original frontend 245 variant; qualification unknown."""


def solve(wordsDict, word1: str, word2: str) -> int:
    same = word1 == word2
    i1 = i2 = -1
    ans = len(wordsDict)
    for i, w in enumerate(wordsDict):
        if same:
            if w == word1:
                if i1 != -1 and i - i1 < ans:
                    ans = i - i1
                i1 = i
        else:
            if w == word1:
                i1 = i
                if i2 != -1 and i1 - i2 < ans:
                    ans = i1 - i2
            elif w == word2:
                i2 = i
                if i1 != -1 and i2 - i1 < ans:
                    ans = i2 - i1
    return ans


shortestWordDistance = solve


class Solution:
    def shortestWordDistance(self, wordsDict, word1: str, word2: str) -> int:
        return solve(wordsDict, word1, word2)
