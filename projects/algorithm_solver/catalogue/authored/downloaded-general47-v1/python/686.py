"""686. Repeated String Match (Medium).

Specification: https://leetcode.com/problems/repeated-string-match/description/
"""


def solve(a: str, b: str) -> int:
    repeated = a
    count = 1
    while len(repeated) < len(b):
        repeated += a
        count += 1
    if b in repeated:
        return count
    repeated += a
    if b in repeated:
        return count + 1
    return -1


class Solution:
    def repeatedStringMatch(self, a: str, b: str) -> int:
        return solve(a, b)
