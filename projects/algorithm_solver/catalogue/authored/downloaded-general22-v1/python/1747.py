"""1747. Lexicographically Smallest String After Applying Operations (Medium).

Specification: https://leetcode.com/problems/lexicographically-smallest-string-after-applying-operations/description/
"""


def solve(s: str, a: int, b: int) -> str:
    n = len(s)
    seen = {s}
    queue = [s]
    best = s
    while queue:
        cur = queue.pop(0)
        best = min(best, cur)
        added = "".join(str((int(ch) + a) % 10) if i % 2 == 1 else ch for i, ch in enumerate(cur))
        if added not in seen:
            seen.add(added)
            queue.append(added)
        rotated = cur if b % n == 0 else cur[-(b % n):] + cur[:n - (b % n)]
        if rotated not in seen:
            seen.add(rotated)
            queue.append(rotated)
    return best


class Solution:
    def findLexSmallestString(self, s: str, a: int, b: int) -> str:
        return solve(s, a, b)
