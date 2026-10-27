# Original implementation. Contract: https://leetcode.com/problems/count-positions-on-street-with-required-brightness/
def solve(n,lights,requirement):
    d=[0]*(n+1)
    for x,r in lights:d[max(0,x-r)]+=1;d[min(n,x+r+1)]-=1
    active=out=0
    for i in range(n):active+=d[i];out+=active>=requirement[i]
    return out
