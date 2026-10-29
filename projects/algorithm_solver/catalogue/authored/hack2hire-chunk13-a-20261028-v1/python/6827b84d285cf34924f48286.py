"""Hack2Hire 6827b84d285cf34924f48286 (Pin Board Connectivity, variant 1) over an INFERRED spec; qualification unknown."""


def solve(boards, pin1, pin2):
    parent = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for board in boards:
        for pin in board:
            if pin not in parent:
                parent[pin] = pin
        root = find(board[0])
        for pin in board[1:]:
            other = find(pin)
            if other != root:
                parent[other] = root
    if pin1 not in parent or pin2 not in parent:
        return False
    return find(pin1) == find(pin2)


class Solution:
    def arePinsRelated(self, boards, pin1, pin2):
        return solve(boards, pin1, pin2)
