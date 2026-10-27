# Original implementation. Contract: https://leetcode.com/problems/brightest-position-on-street/
from collections import Counter
def solve(lights):
    delta=Counter()
    for x,r in lights:delta[x-r]+=1;delta[x+r+1]-=1
    best=-1;active=0;answer=0
    for x in sorted(delta):
        active+=delta[x]
        if active>best:best=active;answer=x
    return answer
