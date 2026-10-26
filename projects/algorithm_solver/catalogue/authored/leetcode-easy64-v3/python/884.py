"""884. Uncommon Words from Two Sentences (Easy).

Specification: https://leetcode.com/problems/uncommon-words-from-two-sentences/description/
"""


def solve(s1: str, s2: str) -> list[str]:
    """O(L) expected time and O(L) space for total text length L; preserve inputs."""
    counts = {}
    for sentence in (s1, s2):
        for word in sentence.split():
            counts[word] = counts.get(word, 0) + 1
    result = []
    for word, count in counts.items():
        if count == 1:
            result.append(word)
    return result


class Solution:
    def uncommonFromSentences(self, s1: str, s2: str) -> list[str]:
        return solve(s1, s2)
