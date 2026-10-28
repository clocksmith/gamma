"""937. Reorder Data in Log Files (Medium).

Specification: https://leetcode.com/problems/reorder-data-in-log-files/description/
"""


def solve(logs: list[str]) -> list[str]:
    letter = []
    digit = []
    for log in logs:
        space = log.index(' ')
        rest = log[space + 1:]
        if rest[0].isdigit():
            digit.append(log)
        else:
            letter.append(log)
    letter.sort(key=lambda log: (log[log.index(' ') + 1:], log[:log.index(' ')]))
    return letter + digit


class Solution:
    def reorderLogFiles(self, logs: list[str]) -> list[str]:
        return solve(logs)
