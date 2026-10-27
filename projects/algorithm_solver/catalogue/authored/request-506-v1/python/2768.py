# Original implementation. Contract: https://leetcode.com/problems/number-of-black-blocks/
from collections import Counter
def solve(m,n,coordinates):
    blocks=Counter()
    for x,y in coordinates:
        for a in (x-1,x):
            for b in (y-1,y):
                if 0<=a<m-1 and 0<=b<n-1:blocks[a,b]+=1
    out=[(m-1)*(n-1)-len(blocks),0,0,0,0]
    for c in blocks.values():out[c]+=1
    return out
