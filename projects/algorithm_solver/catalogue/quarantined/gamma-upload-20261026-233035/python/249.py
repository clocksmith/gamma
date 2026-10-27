"""249. Group Shifted Strings."""
from collections import defaultdict

def solve(strings: list[str]) -> list[list[str]]:
    groups = defaultdict(list)
    for word in strings:
        key = tuple((ord(char) - ord(word[0])) % 26 for char in word)
        groups[key].append(word)
    return list(groups.values())

class Solution:
    def groupStrings(self, strings: list[str]) -> list[list[str]]:
        return solve(strings)
