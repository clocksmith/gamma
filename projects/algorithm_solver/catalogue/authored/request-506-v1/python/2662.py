# Original candidate. Contract: https://leetcode.com/problems/minimum-cost-of-a-path-with-special-roads/
def solve(start, target, specialRoads):
    roads=specialRoads;n=len(roads);dist=[abs(start[0]-r[0])+abs(start[1]-r[1])+r[4] for r in roads];used=[False]*n
    answer=abs(start[0]-target[0])+abs(start[1]-target[1])
    for _ in range(n):
        u=min((j for j in range(n) if not used[j]),key=lambda j:dist[j]);used[u]=True;x,y=roads[u][2:4]
        answer=min(answer,dist[u]+abs(x-target[0])+abs(y-target[1]))
        for v,r in enumerate(roads):dist[v]=min(dist[v],dist[u]+abs(x-r[0])+abs(y-r[1])+r[4])
    return answer
