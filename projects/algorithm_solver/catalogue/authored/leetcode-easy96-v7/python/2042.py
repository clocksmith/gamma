"""2042. Check if Numbers Are Ascending in a Sentence (Easy).

Specification: https://leetcode.com/problems/check-if-numbers-are-ascending-in-a-sentence/description/
"""


def solve(s: str) -> bool:
    """O(n) time and token space; compare only numeric tokens in the stated sentence domain."""
    previous = -1
    for token in s.split(' '):
        if not ('0' <= token[0] <= '9'):
            continue
        value = int(token)
        if value <= previous:
            return False
        previous = value
    return True


class Solution:
    def areNumbersAscending(self, s: str) -> bool:
        return solve(s)
