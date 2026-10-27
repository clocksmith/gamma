"""49. Group Anagrams."""
from collections import defaultdict

def solve(strs: list[str]) -> list[list[str]]:
    groups = defaultdict(list)
    for word in strs:
        groups[tuple(sorted(word))].append(word)
    return list(groups.values())

class Solution:
    def groupAnagrams(self, strs: list[str]) -> list[list[str]]:
        return solve(strs)
