"""Original candidate; no qualification or admission."""

def solve(n,restrictions):
    rows=sorted([[i,h] for i,h in restrictions]+[[1,0]])
    for i in range(1,len(rows)):rows[i][1]=min(rows[i][1],rows[i-1][1]+rows[i][0]-rows[i-1][0])
    for i in range(len(rows)-2,-1,-1):rows[i][1]=min(rows[i][1],rows[i+1][1]+rows[i+1][0]-rows[i][0])
    best=rows[-1][1]+n-rows[-1][0]
    for (a,h),(b,k) in zip(rows,rows[1:]):best=max(best,(h+k+b-a)//2)
    return best


class Solution:
    def maxBuilding(self, n, restrictions):
        return solve(n, restrictions)
