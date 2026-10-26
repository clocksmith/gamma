"""2061. Number of Spaces Cleaning Robot Cleaned: stop at the first repeated position-and-direction state."""


def solve(room: list[list[int]]) -> int:
    """O(r * c) time and O(r * c) auxiliary space; inputs are read-only."""
    rows, columns = len(room), len(room[0])
    states = [0] * (rows * columns)
    directions = ((0, 1), (1, 0), (0, -1), (-1, 0))
    row = column = direction = cleaned = 0
    while True:
        index = row * columns + column
        bit = 1 << direction
        if states[index] & bit:
            return cleaned
        if states[index] == 0:
            cleaned += 1
        states[index] |= bit
        dr, dc = directions[direction]
        next_row, next_column = row + dr, column + dc
        if 0 <= next_row < rows and 0 <= next_column < columns and room[next_row][next_column] == 0:
            row, column = next_row, next_column
        else:
            direction = (direction + 1) % 4


class Solution:
    def numberOfCleanRooms(self, room: list[list[int]]) -> int:
        return solve(room)
