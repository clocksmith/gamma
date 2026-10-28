"""841. Keys and Rooms (Medium).

Specification: https://leetcode.com/problems/keys-and-rooms/description/
"""


def solve(rooms: list[list[int]]) -> bool:
    visited = {0}
    stack = [0]
    while stack:
        room = stack.pop()
        for key in rooms[room]:
            if key not in visited:
                visited.add(key)
                stack.append(key)
    return len(visited) == len(rooms)


class Solution:
    def canVisitAllRooms(self, rooms: list[list[int]]) -> bool:
        return solve(rooms)
