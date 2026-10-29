"""Original frontend 374 variant; qualification unknown."""


def solve(n: int, pick=None) -> int:
    low = 1
    high = int(n)
    g = globals().get("guess") if pick is None else None
    while low <= high:
        mid = (low + high) // 2
        if pick is not None:
            res = 0 if mid == pick else (-1 if mid > pick else 1)
        elif g is not None:
            res = g(mid)
        else:
            return mid
        if res == 0:
            return mid
        if res < 0:
            high = mid - 1
        else:
            low = mid + 1
    return low


guessNumber = solve


class Solution:
    def guessNumber(self, n: int, pick=None) -> int:
        return solve(n, pick)
