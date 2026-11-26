def solve(V,E,r,edges):
    cost=[-float('inf')]*V
    cost[r]=0
    for _ in range(V-1):
        for edge in edges:
            s=edge[0]
            t=edge[1]
            d=edge[2]
            if cost[t]<cost[s]+d:
                cost[t]=cost[s]+d
    ans=cost[V-1]
    for _ in range(V-1):
        for edge in edges:
            s=edge[0]
            t=edge[1]
            d=edge[2]
            if cost[t]<cost[s]+d:
                cost[t]=cost[s]+d
    if ans!=cost[V-1]:
        return float('inf')
    return ans
            



V,E=map(int,input().split())
edges=[]
for _ in range(E):
    s,t,d=map(int,input().split())
    s-=1
    t-=1
    edges.append(tuple((s,t,d)))
ans=solve(V,E,0,edges)
if ans==float('inf'):
    print("inf")
else:
    print(ans)