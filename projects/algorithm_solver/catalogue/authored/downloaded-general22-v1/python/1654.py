"""1654. Minimum Jumps to Reach Home (Medium).

Specification: https://leetcode.com/problems/minimum-jumps-to-reach-home/description/
"""


def solve(forbidden: list[int], a: int, b: int, x: int) -> int:
    blocked = set(forbidden)
    bound = max([x] + forbidden + [0]) + a + b + 100
    queue = [(0, False, 0)]
    visited = {(0, False)}
    while queue:
        pos, backward, steps = queue.pop(0)
        if pos == x:
            return steps
        forward = pos + a
        if forward <= bound and forward not in blocked and (forward, False) not in visited:
            visited.add((forward, False))
            queue.append((forward, False, steps + 1))
        if not backward:
            back = pos - b
            if back >= 0 and back not in blocked and (back, True) not in visited:
                visited.add((back, True))
                queue.append((back, True, steps + 1))
    return -1


class Solution:
    def minimumJumps(self, forbidden: list[int], a: int, b: int, x: int) -> int:
        return solve(forbidden, a, b, x)
