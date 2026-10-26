"""1503. Last Moment Before All Ants Fall Out of a Plank: treat colliding ants as exchanging identities."""


def solve(n: int, left: list[int], right: list[int]) -> int:
    """O(|left| + |right|) time and O(1) auxiliary space; inputs are read-only."""
    answer = 0
    for position in left:
        answer = max(answer, position)
    for position in right:
        answer = max(answer, n - position)
    return answer


class Solution:
    def getLastMoment(self, n: int, left: list[int], right: list[int]) -> int:
        return solve(n, left, right)
