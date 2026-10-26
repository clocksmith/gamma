"""1813. Sentence Similarity III: cover the shorter sentence with matching prefix and suffix words."""


def solve(sentence1: str, sentence2: str) -> bool:
    """O(len(sentence1) + len(sentence2)) time and auxiliary space; inputs are read-only."""
    first = sentence1.split()
    second = sentence2.split()
    if len(first) > len(second):
        first, second = second, first
    prefix = 0
    while prefix < len(first) and first[prefix] == second[prefix]:
        prefix += 1
    suffix = 0
    while suffix < len(first) - prefix and first[-1 - suffix] == second[-1 - suffix]:
        suffix += 1
    return prefix + suffix == len(first)


class Solution:
    def areSentencesSimilar(self, sentence1: str, sentence2: str) -> bool:
        return solve(sentence1, sentence2)
