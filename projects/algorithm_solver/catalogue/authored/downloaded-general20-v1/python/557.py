"""557. Reverse Words in a String III (Easy).

Specification: https://leetcode.com/problems/reverse-words-in-a-string-iii/description/
"""


def solve(s: str) -> str:
    return " ".join(word[::-1] for word in s.split(" "))


class Solution:
    def reverseWords(self, s: str) -> str:
        return solve(s)
