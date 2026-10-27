"""245. Shortest Word Distance III."""
def solve(wordsDict: list[str], word1: str, word2: str) -> int:
    previous = -1
    first = second = -1
    best = len(wordsDict)
    if word1 == word2:
        for index, word in enumerate(wordsDict):
            if word == word1:
                if previous >= 0:
                    best = min(best, index - previous)
                previous = index
        return best
    for index, word in enumerate(wordsDict):
        if word == word1:
            first = index
        elif word == word2:
            second = index
        if first >= 0 and second >= 0:
            best = min(best, abs(first - second))
    return best

class Solution:
    def shortestWordDistance(self, wordsDict, word1, word2):
        return solve(wordsDict, word1, word2)
