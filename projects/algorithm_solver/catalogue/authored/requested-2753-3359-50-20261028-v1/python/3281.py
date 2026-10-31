"""Original frontend 3281 variant; qualification unknown."""


def solve(start, d: int) -> int:
    arr = sorted(start)
    lo, hi = 0, arr[-1] + d - arr[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        prev = arr[0]
        ok = True
        for i in range(1, len(arr)):
            nxt = max(prev + mid, arr[i])
            if nxt > arr[i] + d:
                ok = False
                break
            prev = nxt
        if ok:
            lo = mid
        else:
            hi = mid - 1
    return lo


maxPossibleScore = solve


class Solution:
    def maxPossibleScore(self, start, d: int) -> int:
        return solve(start, d)
