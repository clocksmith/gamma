"""734. Sentence Similarity (Easy).

Specification: https://leetcode.com/problems/sentence-similarity/description/
"""


def solve(sentence1: list[str], sentence2: list[str], similarPairs: list[list[str]]) -> bool:
    """O(n + p) expected word operations, O(p) space; similarity is symmetric, not transitive."""
    if len(sentence1) != len(sentence2):
        return False
    neighbors = {}
    for first, second in similarPairs:
        neighbors.setdefault(first, set()).add(second)
        neighbors.setdefault(second, set()).add(first)
    for first, second in zip(sentence1, sentence2):
        if first != second and second not in neighbors.get(first, ()):
            return False
    return True


class Solution:
    def areSentencesSimilar(self, sentence1: list[str], sentence2: list[str], similarPairs: list[list[str]]) -> bool:
        return solve(sentence1, sentence2, similarPairs)
