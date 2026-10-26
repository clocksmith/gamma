"""3317. Find the Number of Possible Ways for an Event: count assignments by the number of occupied labeled stages."""


def solve(n: int, x: int, y: int) -> int:
    """O(n*min(n,x)) time and O(min(n,x)) auxiliary space. Inputs are preserved."""
    modulus = 1_000_000_007
    size = min(n, x)
    ways = [0] * (size + 1)
    ways[0] = 1
    for performer in range(1, n + 1):
        for occupied in range(min(performer, size), 0, -1):
            ways[occupied] = (occupied * ways[occupied] + (x - occupied + 1) * ways[occupied - 1]) % modulus
        ways[0] = 0
    answer = 0
    scores = 1
    for occupied in range(1, size + 1):
        scores = scores * y % modulus
        answer = (answer + ways[occupied] * scores) % modulus
    return answer


class Solution:
    def numberOfWays(self, n: int, x: int, y: int) -> int:
        return solve(n, x, y)
