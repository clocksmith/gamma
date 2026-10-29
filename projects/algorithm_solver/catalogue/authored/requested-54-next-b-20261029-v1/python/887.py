"""Original move-coverage development candidate; qualification unknown."""
def solve(k, n):
    reachable = [0]*(k+1)
    moves = 0
    while reachable[k] < n:
        moves += 1
        for eggs in range(k,0,-1):
            reachable[eggs] = min(n,reachable[eggs]+reachable[eggs-1]+1)
    return moves

class Solution:
    def superEggDrop(self, k, n):
        return solve(k,n)
