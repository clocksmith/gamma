class Solution:
    def minimumMoves(self, s: str) -> int:
        index = 0
        moves = 0
        while index < len(s):
            if s[index] == "X":
                moves += 1
                index += 3
            else:
                index += 1
        return moves
