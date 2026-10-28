"""151. Reverse Words in a String (Medium).

Specification: https://leetcode.com/problems/reverse-words-in-a-string/description/
"""


def solve(s: str) -> str:
    return " ".join(reversed(s.split()))


class Solution:
    def reverseWords(self, s: str) -> str:
        return solve(s)
