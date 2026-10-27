"""Original candidate for LeetCode 2998. Contract: https://leetcode.com/problems/minimum-number-of-operations-to-make-x-and-y-equal/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(x) time and space when x>y, else O(1); bound exceeds direct decrement path budget"""
from collections import deque

def solve(x,y):
    if x<=y:return y-x
    limit=2*x+11;queue=deque([(x,0)]);seen={x}
    while queue:
        v,d=queue.popleft()
        if v==y:return d
        choices=[v-1,v+1]
        if v%5==0:choices.append(v//5)
        if v%11==0:choices.append(v//11)
        for w in choices:
            if 0<=w<=limit and w not in seen:seen.add(w);queue.append((w,d+1))
