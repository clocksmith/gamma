"""Hack2Hire 6795a8a1010c9ed2f849b1fd (Find Word Path) over an INFERRED spec; qualification unknown."""


def solve(word):
    out, row, col = [], 0, 0
    for ch in word:
        target_row, target_col = divmod(ord(ch) - 97, 5)
        # up and left before down and right keeps the cursor on the board around 'z'
        if target_row < row:
            out.append('U' * (row - target_row))
        if target_col < col:
            out.append('L' * (col - target_col))
        if target_row > row:
            out.append('D' * (target_row - row))
        if target_col > col:
            out.append('R' * (target_col - col))
        out.append('!')
        row, col = target_row, target_col
    return ''.join(out)


class Solution:
    def findWordPath(self, word):
        return solve(word)
