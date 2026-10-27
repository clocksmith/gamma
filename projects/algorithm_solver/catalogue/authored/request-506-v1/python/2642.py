# Original candidate. Contract: https://leetcode.com/problems/design-graph-with-shortest-path-calculator/
def solve(operations, arguments):
    graph=[];out=[]
    for op,a in zip(operations,arguments):
        if op=='Graph':
            n,edges=a;graph=[[] for _ in range(n)]
            for u,v,w in edges:graph[u].append((v,w))
            out.append(None)
        elif op=='addEdge':u,v,w=a[0];graph[u].append((v,w));out.append(None)
        elif op=='shortestPath':
            s,t=a;n=len(graph);dist=[float('inf')]*n;dist[s]=0;used=[False]*n
            for _ in range(n):
                u=min((i for i in range(n) if not used[i]),key=lambda i:dist[i],default=-1)
                if u<0 or dist[u]==float('inf'):break
                used[u]=True
                for v,w in graph[u]:dist[v]=min(dist[v],dist[u]+w)
            out.append(-1 if dist[t]==float('inf') else dist[t])
        else:raise ValueError('unknown operation')
    return out
