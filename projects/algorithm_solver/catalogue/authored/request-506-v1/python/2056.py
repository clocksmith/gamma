"""Original candidate for LeetCode 2056. Contract: https://leetcode.com/problems/number-of-valid-move-combinations-on-chessboard/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(28^n*n*8) upper bound, O(n*28*8) space; n <= 4, at most one queen"""
def solve(pieces,positions):
    straight=[(1,0),(-1,0),(0,1),(0,-1)];diagonal=[(1,1),(1,-1),(-1,1),(-1,-1)]
    options=[]
    for piece,(r,c) in zip(pieces,positions):
        paths=[[(r,c)]*8]
        dirs=straight if piece=='rook' else diagonal if piece=='bishop' else straight+diagonal
        for dr,dc in dirs:
            for steps in range(1,8):
                if not(1<=r+dr*steps<=8 and 1<=c+dc*steps<=8):break
                paths.append([(r+dr*min(t,steps),c+dc*min(t,steps)) for t in range(8)])
        options.append(paths)
    chosen=[]
    def visit(i):
        if i==len(pieces):return 1
        count=0
        for path in options[i]:
            if all(all(path[t]!=old[t] for t in range(8)) for old in chosen):
                chosen.append(path);count+=visit(i+1);chosen.pop()
        return count
    return visit(0)
