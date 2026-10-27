# Original candidate implementation. Contract: https://leetcode.com/problems/shortest-string-that-contains-three-strings/
from itertools import permutations

def solve(a,b,c):
    def merge(x,y):
        if y in x: return x
        for overlap in range(min(len(x),len(y)),0,-1):
            if x[-overlap:]==y[:overlap]: return x+y[overlap:]
        return x+y
    candidates=[merge(merge(x,y),z) for x,y,z in permutations((a,b,c))]
    return min(candidates,key=lambda s:(len(s),s))
