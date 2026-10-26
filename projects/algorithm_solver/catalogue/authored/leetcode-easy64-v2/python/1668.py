"""1668. Maximum Repeating Substring (Easy).

Specification: https://leetcode.com/problems/maximum-repeating-substring/description/
"""


def solve(sequence: str, word: str) -> int:
    """O(n * m) time, O(n) space; n=len(sequence), m=len(word)."""
    length = len(word)
    repetitions = [0] * (len(sequence) + 1)
    result = 0
    for end in range(length, len(sequence) + 1):
        if sequence.startswith(word, end - length):
            repetitions[end] = repetitions[end - length] + 1
            result = max(result, repetitions[end])
    return result


class Solution:
    def maxRepeating(self, sequence: str, word: str) -> int:
        return solve(sequence, word)
