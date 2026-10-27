# Original candidate implementation. Contract: https://leetcode.com/problems/match-alphanumerical-pattern-in-matrix-i/
def solve(board,pattern):
    rows,cols=len(pattern),len(pattern[0])
    for top in range(len(board)-rows+1):
        for left in range(len(board[0])-cols+1):
            forward={};reverse={};ok=True
            for r in range(rows):
                for c in range(cols):
                    ch=pattern[r][c];value=board[top+r][left+c]
                    if ch.isdigit() and int(ch)!=value:ok=False;break
                    if ch in forward and forward[ch]!=value or value in reverse and reverse[value]!=ch:ok=False;break
                    forward[ch]=value;reverse[value]=ch
                if not ok:break
            if ok:return [top,left]
    return [-1,-1]
