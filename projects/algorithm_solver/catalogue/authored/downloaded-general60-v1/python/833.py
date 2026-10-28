"""833. Find And Replace in String (Medium).

Specification: https://leetcode.com/problems/find-and-replace-in-string/description/
"""


def solve(s: str, indices: list[int], sources: list[str], targets: list[str]) -> str:
    replacements = sorted(zip(indices, sources, targets), key=lambda item: -item[0])
    result = s
    for index, source, target in replacements:
        if result[index:index + len(source)] == source:
            result = result[:index] + target + result[index + len(source):]
    return result


class Solution:
    def findReplaceString(self, s: str, indices: list[int], sources: list[str], targets: list[str]) -> str:
        return solve(s, indices, sources, targets)
