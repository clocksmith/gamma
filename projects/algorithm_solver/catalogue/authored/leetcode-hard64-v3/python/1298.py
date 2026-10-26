"""1298. Maximum Candies You Can Get from Boxes: reachability with independent possession and key state; O(boxes+references) time and space."""

from collections import deque


def solve(status: list[int], candies: list[int], keys: list[list[int]], containedBoxes: list[list[int]], initialBoxes: list[int]) -> int:
    available = [False] * len(status)
    unlocked = [bool(value) for value in status]
    opened = [False] * len(status)
    queue = deque()
    for box in initialBoxes:
        available[box] = True
        if unlocked[box]:
            queue.append(box)
    total = 0
    while queue:
        box = queue.popleft()
        if opened[box]:
            continue
        opened[box] = True
        total += candies[box]
        for key in keys[box]:
            if not unlocked[key]:
                unlocked[key] = True
                if available[key] and not opened[key]:
                    queue.append(key)
        for child in containedBoxes[box]:
            if not available[child]:
                available[child] = True
                if unlocked[child] and not opened[child]:
                    queue.append(child)
    return total


class Solution:
    def maxCandies(self, status: list[int], candies: list[int], keys: list[list[int]], containedBoxes: list[list[int]], initialBoxes: list[int]) -> int:
        return solve(status, candies, keys, containedBoxes, initialBoxes)
