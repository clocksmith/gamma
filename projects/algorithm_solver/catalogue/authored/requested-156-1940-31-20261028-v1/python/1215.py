"""Original frontend 1215 variant; qualification unknown."""

from collections import deque


def solve(low: int, high: int):
    res = [0] if low == 0 else []
    q = deque(range(1, 10))
    while q:
        v = q.popleft()
        if v > high:
            continue
        if v >= low:
            res.append(v)
        last = v % 10
        if last > 0 and v * 10 + last - 1 <= high:
            q.append(v * 10 + last - 1)
        if last < 9 and v * 10 + last + 1 <= high:
            q.append(v * 10 + last + 1)
    return sorted(res)


countSteppingNumbers = solve


class Solution:
    def countSteppingNumbers(self, low: int, high: int):
        return solve(low, high)
