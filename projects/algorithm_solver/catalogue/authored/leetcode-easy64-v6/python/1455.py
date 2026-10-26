"""1455. Check If a Word Occurs As a Prefix of Any Word in a Sentence (Easy).

Specification: https://leetcode.com/problems/check-if-a-word-occurs-as-a-prefix-of-any-word-in-a-sentence/description/
"""


def solve(sentence: str, searchWord: str) -> int:
    """O(len(sentence) + len(searchWord)) time, O(len(sentence)) space; return a one-based index."""
    words = sentence.split(' ')
    for index, word in enumerate(words):
        if word.startswith(searchWord):
            return index + 1
    return -1


class Solution:
    def isPrefixOfWord(self, sentence: str, searchWord: str) -> int:
        return solve(sentence, searchWord)
