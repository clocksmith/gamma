"""Original candidate for LeetCode 2664. Contract: https://leetcode.com/problems/the-knights-tour/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(8^(mn)) worst-case time, O(mn) space; complete backtracking, Warnsdorff ordering, mn<=25"""
def solve(m,n,r,c):
    board=[[-1]*n for _ in range(m)];moves=[(1,2),(1,-2),(-1,2),(-1,-2),(2,1),(2,-1),(-2,1),(-2,-1)]
    def nexts(a,b):return [(a+x,b+y) for x,y in moves if 0<=a+x<m and 0<=b+y<n and board[a+x][b+y]<0]
    def search(a,b,t):
        board[a][b]=t
        if t==m*n-1:return True
        for x,y in sorted(nexts(a,b),key=lambda p:len(nexts(*p))):
            if search(x,y,t+1):return True
        board[a][b]=-1;return False
    if not search(r,c,0):raise ValueError('No tour; outside guaranteed-solvable contract')
    return board
