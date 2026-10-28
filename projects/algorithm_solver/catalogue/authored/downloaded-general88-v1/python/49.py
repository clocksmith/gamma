"""49. Group Anagrams (Medium).

Specification: https://leetcode.com/problems/group-anagrams/description/
"""


def solve(strs: list[str]) -> list[list[str]]:
    groups = {}
    for word in strs:
        key = "".join(sorted(word))
        groups.setdefault(key, []).append(word)
    result = [sorted(group) for group in groups.values()]
    result.sort(key=lambda group: ",".join(group))
    return result


class Solution:
    def groupAnagrams(self, strs: list[str]) -> list[list[str]]:
        return solve(strs)
