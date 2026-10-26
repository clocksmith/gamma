"""2092. Find All People With Secret."""

from collections import defaultdict, deque


def solve(n: int, meetings: list[list[int]], firstPerson: int) -> list[int]:
    """Time-grouped propagation through each simultaneous meeting graph; O(M log M+n) time, O(M+n) space. Inputs are preserved."""
    knows = [False] * n
    knows[0] = knows[firstPerson] = True
    ordered = sorted(meetings, key=lambda meeting: meeting[2])
    cursor = 0
    while cursor < len(ordered):
        end = cursor
        neighbors = defaultdict(list)
        while end < len(ordered) and ordered[end][2] == ordered[cursor][2]:
            first, second, _ = ordered[end]
            neighbors[first].append(second)
            neighbors[second].append(first)
            end += 1
        queue = deque(person for person in neighbors if knows[person])
        reached = set(queue)
        while queue:
            person = queue.popleft()
            for target in neighbors[person]:
                if target not in reached:
                    reached.add(target)
                    knows[target] = True
                    queue.append(target)
        cursor = end
    return [person for person, informed in enumerate(knows) if informed]


class Solution:
    def findAllPeople(self, n: int, meetings: list[list[int]], firstPerson: int) -> list[int]:
        return solve(n, meetings, firstPerson)
