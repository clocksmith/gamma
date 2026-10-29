"""Original frontend 483 variant; qualification unknown."""


def solve(n: str) -> str:
    N = int(n)
    max_m = N.bit_length()
    for m in range(max_m, 1, -1):
        low = 2
        high = int(N ** (1.0 / m)) + 2
        if high >= N:
            high = N - 1
        while low <= high:
            mid = (low + high) // 2
            total = 1
            cur = 1
            for _ in range(m):
                cur *= mid
                total += cur
                if total > N:
                    break
            if total == N:
                return str(mid)
            if total < N:
                low = mid + 1
            else:
                high = mid - 1
    return str(N - 1)


smallestGoodBase = solve


class Solution:
    def smallestGoodBase(self, n: str) -> str:
        return solve(n)
