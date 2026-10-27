"""243. Shortest Word Distance."""
def solve(wordsDict: list[str], word1: str, word2: str) -> int:
    first = second = -1
    best = len(wordsDict)
    for index, word in enumerate(wordsDict):
        if word == word1:
            first = index
        elif word == word2:
            second = index
        if first >= 0 and second >= 0:
            best = min(best, abs(first - second))
    return best

class Solution:
    def shortestDistance(self, wordsDict, word1, word2):
        return solve(wordsDict, word1, word2)
