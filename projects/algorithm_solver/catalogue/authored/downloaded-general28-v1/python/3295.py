"""3295. Report Spam Message (Easy).

Specification: https://leetcode.com/problems/report-spam-message/description/
"""


def solve(message: list[str], bannedWords: list[str]) -> bool:
    banned = set(bannedWords)
    matches = sum(1 for w in message if w in banned)
    return matches >= 2


class Solution:
    def reportSpam(self, message: list[str], bannedWords: list[str]) -> bool:
        return solve(message, bannedWords)
