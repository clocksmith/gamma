"""1318. Minimum Flips to Make a OR b Equal to c: count required changes independently at each bit."""


def solve(a: int, b: int, c: int) -> int:
    """O(log(max(a, b, c) + 1)) time and O(1) auxiliary space; inputs are read-only."""
    answer = 0
    while a or b or c:
        first, second, target = a & 1, b & 1, c & 1
        if target:
            answer += int(first == 0 and second == 0)
        else:
            answer += first + second
        a >>= 1
        b >>= 1
        c >>= 1
    return answer


class Solution:
    def minFlips(self, a: int, b: int, c: int) -> int:
        return solve(a, b, c)
