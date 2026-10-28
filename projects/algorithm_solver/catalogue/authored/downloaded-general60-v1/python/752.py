"""752. Open the Lock (Medium).

Specification: https://leetcode.com/problems/open-the-lock/description/
"""


def solve(deadends: list[str], target: str) -> int:
    dead = set(deadends)
    if '0000' in dead:
        return -1
    if target == '0000':
        return 0
    queue = ['0000']
    visited = {'0000'}
    steps = 0
    while queue:
        steps += 1
        next_queue = []
        for current in queue:
            for i in range(4):
                for delta in (-1, 1):
                    digit = (int(current[i]) + delta) % 10
                    candidate = current[:i] + str(digit) + current[i + 1:]
                    if candidate == target:
                        return steps
                    if candidate not in dead and candidate not in visited:
                        visited.add(candidate)
                        next_queue.append(candidate)
        queue = next_queue
    return -1


class Solution:
    def openLock(self, deadends: list[str], target: str) -> int:
        return solve(deadends, target)
