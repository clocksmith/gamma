"""2350. Shortest Impossible Sequence of Rolls."""


def solve(rolls: list[int], k: int) -> int:
    """Greedily finish complete alphabet blocks; O(n+k) time and O(k) space. Inputs are preserved."""
    seen = set()
    answer = 1
    for value in rolls:
        seen.add(value)
        if len(seen) == k:
            answer += 1
            seen.clear()
    return answer


class Solution:
    def shortestSequence(self, rolls: list[int], k: int) -> int:
        return solve(rolls, k)
