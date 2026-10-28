"""1487. Making File Names Unique (Medium).

Specification: https://leetcode.com/problems/making-file-names-unique/description/
"""


def solve(names: list[str]) -> list[str]:
    used = set()
    next_suffix = {}
    result = []
    for name in names:
        if name not in used:
            used.add(name)
            next_suffix[name] = 1
            result.append(name)
            continue
        suffix = next_suffix.get(name, 1)
        while f"{name}({suffix})" in used:
            suffix += 1
        unique = f"{name}({suffix})"
        used.add(unique)
        next_suffix[name] = suffix + 1
        next_suffix[unique] = 1
        result.append(unique)
    return result


class Solution:
    def getFolderNames(self, names: list[str]) -> list[str]:
        return solve(names)
