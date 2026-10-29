"""Hack2Hire 6a21c269d5c5b3e5f9c34546 (Find Valid Tile Moves) over an INFERRED spec; qualification unknown."""


def solve(start, target):
    if sorted(start) != sorted(target):
        return False
    goal = ''.join(target)
    first = ''.join(start)
    seen = {first}
    stack = [first]
    n = len(first)
    while stack:
        board = stack.pop()
        if board == goal:
            return True
        for i, tile in enumerate(board):
            if tile == 'R':
                if i + 1 < n and board[i + 1] == '_':
                    nxt = board[:i] + '_R' + board[i + 2:]
                elif i + 2 < n and board[i + 1] == 'B' and board[i + 2] == '_':
                    nxt = board[:i] + '_B' + 'R' + board[i + 3:]
                else:
                    continue
            elif tile == 'B':
                if i >= 1 and board[i - 1] == '_':
                    nxt = board[:i - 1] + 'B_' + board[i + 1:]
                elif i >= 2 and board[i - 1] == 'R' and board[i - 2] == '_':
                    nxt = board[:i - 2] + 'BR_' + board[i + 1:]
                else:
                    continue
            else:
                continue
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return False


class Solution:
    def canReach(self, start, target):
        return solve(start, target)
