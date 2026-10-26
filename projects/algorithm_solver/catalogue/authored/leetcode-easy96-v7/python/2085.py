"""2085. Count Common Words With One Occurrence (Easy).

Specification: https://leetcode.com/problems/count-common-words-with-one-occurrence/description/
"""


def solve(words1: list[str], words2: list[str]) -> int:
    """O(total characters) expected time, O(n + m) map entries; preserve both lists."""
    first = {}
    second = {}
    for word in words1:
        first[word] = first.get(word, 0) + 1
    for word in words2:
        second[word] = second.get(word, 0) + 1
    return sum(count == 1 and second.get(word) == 1 for word, count in first.items())


class Solution:
    def countWords(self, words1: list[str], words2: list[str]) -> int:
        return solve(words1, words2)
