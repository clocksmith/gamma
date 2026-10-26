"""1805. Number of Different Integers in a String (Easy).

Specification: https://leetcode.com/problems/number-of-different-integers-in-a-string/description/
"""


def solve(word: str) -> int:
    """O(n) expected time, O(n) space; normalize digit strings without numeric parsing."""
    values = set()
    index = 0
    while index < len(word):
        if not ('0' <= word[index] <= '9'):
            index += 1
            continue
        start = index
        while index < len(word) and '0' <= word[index] <= '9':
            index += 1
        while start < index - 1 and word[start] == '0':
            start += 1
        values.add(word[start:index])
    return len(values)


class Solution:
    def numDifferentIntegers(self, word: str) -> int:
        return solve(word)
