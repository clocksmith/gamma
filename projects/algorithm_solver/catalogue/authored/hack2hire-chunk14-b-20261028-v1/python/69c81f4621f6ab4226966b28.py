"""Hack2Hire 69c81f4621f6ab4226966b28 (Winner in a Dot Grid Game) over an INFERRED spec; qualification unknown."""


def solve(moves):
    horizontal = [[False] * 8 for _ in range(9)]
    vertical = [[False] * 9 for _ in range(8)]
    score = [0, 0]

    def closed(r, c):
        return horizontal[r][c] and horizontal[r + 1][c] and vertical[r][c] and vertical[r][c + 1]

    for k, (r1, c1, r2, c2) in enumerate(moves):
        r, c = min(r1, r2), min(c1, c2)
        gained = 0
        if r1 == r2:
            horizontal[r][c] = True
            if r >= 1 and closed(r - 1, c):
                gained += 1
            if r <= 7 and closed(r, c):
                gained += 1
        else:
            vertical[r][c] = True
            if c >= 1 and closed(r, c - 1):
                gained += 1
            if c <= 7 and closed(r, c):
                gained += 1
        score[k % 2] += gained
    if score[0] == score[1]:
        return 0
    return 1 if score[0] > score[1] else 2


class Solution:
    def dotGridWinner(self, moves):
        return solve(moves)
