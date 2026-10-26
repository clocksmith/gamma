"""2120. Execution of All Suffix Instructions Staying in a Grid: simulate each bounded instruction suffix until its first out-of-grid move."""


def solve(n: int, startPos: list[int], s: str) -> list[int]:
    """O(m^2) time and O(m) result space for at most 500 instructions; inputs are read-only."""
    directions = {'L': (0, -1), 'R': (0, 1), 'U': (-1, 0), 'D': (1, 0)}
    result = [0] * len(s)
    for start in range(len(s)):
        row, column = startPos
        for index in range(start, len(s)):
            dr, dc = directions[s[index]]
            row += dr
            column += dc
            if not (0 <= row < n and 0 <= column < n):
                break
            result[start] += 1
    return result


class Solution:
    def executeInstructions(self, n: int, startPos: list[int], s: str) -> list[int]:
        return solve(n, startPos, s)
