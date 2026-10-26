"""3680. Generate Schedule."""
from __future__ import annotations


def solve(n: int) -> list[list[int]]:
    """O(n^2) time, O(n) auxiliary space excluding the O(n^2) returned schedule."""
    if n < 5:
        return []
    if n == 5:
        first = [[0, 1], [2, 3], [0, 4], [1, 2], [3, 4],
                 [0, 2], [1, 3], [2, 4], [0, 3], [1, 4]]
        orientation = {(min(a, b), max(a, b)): (a, b) for a, b in first}
        answer = [pair.copy() for pair in first]
        for a, b in first:
            a, b = (a + 2) % 5, (b + 2) % 5
            home, away = orientation[(min(a, b), max(a, b))]
            answer.append([away, home])
        return answer
    size = n if n % 2 == 0 else n + 1
    answer = []
    for reverse in (False, True):
        players = list(range(size))
        for _ in range(size - 1):
            matches = []
            for index in range(size // 2):
                a, b = players[index], players[size - index - 1]
                if a < n and b < n:
                    matches.append([b, a] if reverse else [a, b])
            if answer:
                previous = set(answer[-1])
                selected = next(index for index, pair in enumerate(matches)
                                if pair[0] not in previous and pair[1] not in previous)
                matches[0], matches[selected] = matches[selected], matches[0]
            answer.extend(matches)
            players = [players[0], players[-1]] + players[1:-1]
    return answer


class Solution:
    def generateSchedule(self, n: int) -> list[list[int]]:
        return solve(n)
