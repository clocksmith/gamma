"""Original candidate; no qualification or admission."""

def solve(board):
    r,c=next((r,c) for r in range(8) for c in range(8) if board[r][c]=='R');out=0
    for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
        nr,nc=r+dr,c+dc
        while 0<=nr<8 and 0<=nc<8:
            if board[nr][nc]!='.':out+=board[nr][nc]=='p';break
            nr+=dr;nc+=dc
    return out


class Solution:
    def numRookCaptures(self, board):
        return solve(board)
