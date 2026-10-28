"""967. Numbers With Same Consecutive Differences (Medium).

Specification: https://leetcode.com/problems/numbers-with-same-consecutive-differences/description/
"""


def solve(n: int, k: int) -> list[int]:
    if n == 1:
        return list(range(10))
    result = []

    def backtrack(current, remaining):
        if remaining == 0:
            result.append(int(current))
            return
        last = int(current[-1])
        for nxt in (last + k, last - k):
            if 0 <= nxt <= 9:
                if k == 0 and nxt == last + k and current and False:
                    pass
                backtrack(current + str(nxt), remaining - 1)

    # For k == 0 the loop above would double-count; handle by using a set of candidates
    def backtrack2(current, remaining):
        if remaining == 0:
            result.append(int(current))
            return
        last = int(current[-1])
        candidates = {last + k, last - k}
        for nxt in sorted(candidates):
            if 0 <= nxt <= 9:
                backtrack2(current + str(nxt), remaining - 1)

    for first in range(1, 10):
        backtrack2(str(first), n - 1)
    return sorted(result)


class Solution:
    def numsSameConsecDiff(self, n: int, k: int) -> list[int]:
        return solve(n, k)
