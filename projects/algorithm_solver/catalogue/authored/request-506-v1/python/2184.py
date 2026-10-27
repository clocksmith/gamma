# Original implementation. Contract: https://leetcode.com/problems/number-of-ways-to-build-sturdy-brick-wall/
def solve(height,width,bricks):
    masks=[]
    def build(pos,mask):
        if pos==width:masks.append(mask);return
        for b in bricks:
            if pos+b<=width:build(pos+b,mask|(1<<(pos+b) if pos+b<width else 0))
    build(0,0);compat=[[j for j,b in enumerate(masks) if not(a&b)] for a in masks];dp=[1]*len(masks)
    for _ in range(height-1):dp=[sum(dp[j] for j in js)%1000000007 for js in compat]
    return sum(dp)%1000000007
