"""Hack2Hire 69a357a36e73e4abccc9bf9c (Matrix Transformation with Commands) over an INFERRED spec; qualification unknown."""


def solve(matrix, commands):
    n = len(matrix)
    order = list(range(n))
    flipped = [False] * n
    for command in commands:
        parts = command.split(' ')
        if parts[0] == 'reverseRow':
            row = order[int(parts[1])]
            flipped[row] = not flipped[row]
        else:
            a, b = int(parts[1]), int(parts[2])
            order[a], order[b] = order[b], order[a]
    return [matrix[row][::-1] if flipped[row] else list(matrix[row]) for row in order]


class Solution:
    def transformMatrix(self, matrix, commands):
        return solve(matrix, commands)
