"""2201. Count Artifacts That Can Be Extracted (Medium).

Specification: https://leetcode.com/problems/count-artifacts-that-can-be-extracted/description/
"""


def solve(n: int, artifacts: list[list[int]], dig: list[list[int]]) -> int:
    dug = {(r, c) for r, c in dig}
    count = 0
    for r1, c1, r2, c2 in artifacts:
        if all((r, c) in dug for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)):
            count += 1
    return count


class Solution:
    def digArtifacts(self, n, artifacts, dig) -> object:
        return solve(n, artifacts, dig)
