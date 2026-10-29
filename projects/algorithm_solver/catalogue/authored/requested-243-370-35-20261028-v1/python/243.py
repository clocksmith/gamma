"""Original frontend 243 variant; qualification unknown."""


def solve(wordsDict, word1: str, word2: str) -> int:
    i1 = i2 = -1
    ans = len(wordsDict)
    for i, w in enumerate(wordsDict):
        if w == word1:
            i1 = i
            if i2 != -1 and i1 - i2 < ans:
                ans = i1 - i2
        elif w == word2:
            i2 = i
            if i1 != -1 and i2 - i1 < ans:
                ans = i2 - i1
    return ans


shortestDistance = solve


class Solution:
    def shortestDistance(self, wordsDict, word1: str, word2: str) -> int:
        return solve(wordsDict, word1, word2)
