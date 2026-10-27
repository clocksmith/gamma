# Original candidate implementation. Contract: https://leetcode.com/problems/count-pairs-of-points-with-distance-k/
def solve(coordinates,k):
    seen={}; result=0
    for x,y in coordinates:
        for dx in range(k+1): result+=seen.get((x^dx,y^(k-dx)),0)
        seen[x,y]=seen.get((x,y),0)+1
    return result
