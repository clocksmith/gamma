"""288. Unique Word Abbreviation."""
from collections import defaultdict

def abbreviation(word: str) -> str:
    return word if len(word) <= 2 else word[0] + str(len(word) - 2) + word[-1]

class ValidWordAbbr:
    def __init__(self, dictionary: list[str]):
        self.words = defaultdict(set)
        for word in dictionary:
            self.words[abbreviation(word)].add(word)

    def isUnique(self, word: str) -> bool:
        values = self.words[abbreviation(word)]
        return not values or values == {word}

def solve(dictionary: list[str], queries: list[str]) -> list[bool]:
    structure = ValidWordAbbr(dictionary)
    return [structure.isUnique(word) for word in queries]
