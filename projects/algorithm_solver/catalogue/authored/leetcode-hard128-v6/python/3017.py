"""3017. Count the Number of Houses at a Certain Distance II.

For each left endpoint, distance values form at most three integer intervals; O(n) time and space. Counts include both directions.
"""

def solve(n: int, x: int, y: int) -> list[int]:
    x, y = min(x, y), max(x, y)
    changes = [0] * (n + 2)

    def add_interval(left, right):
        if left <= right:
            changes[left] += 1
            changes[right + 1] -= 1

    for first in range(1, n + 1):
        approach = abs(first - x) + 1
        if approach + first >= y:
            add_interval(1, n - first)
            continue
        split = (approach + y + first) // 2
        add_interval(1, split - first)
        add_interval(approach + 1, approach + y - split - 1)
        add_interval(approach, approach + n - y)
    answer = []
    current = 0
    for distance in range(1, n + 1):
        current += changes[distance]
        answer.append(2 * current)
    return answer


class Solution:
    def countOfPairs(self, n: int, x: int, y: int) -> list[int]:
        return solve(n, x, y)
