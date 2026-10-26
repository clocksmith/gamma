"""3799. Word Squares II."""
from __future__ import annotations


def solve(words: list[str]) -> list[list[str]]:
    """O(n^4) time and O(n) auxiliary space excluding returned squares; n <= 15 and output is lexicographically ordered."""
    ordered = sorted(words)
    answer = []
    for top in ordered:
        for left in ordered:
            if left == top or left[0] != top[0]:
                continue
            for right in ordered:
                if right == top or right == left or right[0] != top[3]:
                    continue
                for bottom in ordered:
                    if bottom in (top, left, right):
                        continue
                    if bottom[0] == left[3] and bottom[3] == right[3]:
                        answer.append([top, left, right, bottom])
    return answer


class Solution:
    def wordSquares(self, words: list[str]) -> list[list[str]]:
        return solve(words)
