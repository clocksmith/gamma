def solve(s, k):
    moves = {'U':(0,1), 'D':(0,-1), 'L':(-1,0), 'R':(1,0)}
    x = y = 0
    for c in s[:k]:
        dx,dy = moves[c]
        x += dx
        y += dy
    removed = {(x,y)}
    for i in range(k,len(s)):
        dx,dy = moves[s[i]]
        px,py = moves[s[i-k]]
        x += dx-px
        y += dy-py
        removed.add((x,y))
    return len(removed)

class Solution:
    def distinctPoints(self, s, k):
        return solve(s, k)
