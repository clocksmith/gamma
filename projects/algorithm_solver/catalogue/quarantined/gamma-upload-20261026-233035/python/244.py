"""244. Shortest Word Distance II."""
from collections import defaultdict

class WordDistance:
    def __init__(self, wordsDict: list[str]):
        self.positions = defaultdict(list)
        for index, word in enumerate(wordsDict):
            self.positions[word].append(index)

    def shortest(self, word1: str, word2: str) -> int:
        left = self.positions[word1]
        right = self.positions[word2]
        i = j = 0
        best = float('inf')
        while i < len(left) and j < len(right):
            best = min(best, abs(left[i] - right[j]))
            if left[i] < right[j]:
                i += 1
            else:
                j += 1
        return best

def solve(wordsDict: list[str], queries: list[list[str]]) -> list[int]:
    distance = WordDistance(wordsDict)
    return [distance.shortest(*query) for query in queries]
