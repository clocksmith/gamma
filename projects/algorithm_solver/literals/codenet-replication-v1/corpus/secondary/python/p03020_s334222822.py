def main():
    import sys
    input=sys.stdin.readline
    from collections import deque
    inf=10**12

    class MinCostFlow:
        def __init__(self,n):
            self.n=n
            self.edges=[[] for i in range(n)]
        def add_edge(self,fr,to,cap,cost):
            self.edges[fr].append([to,cap,cost,len(self.edges[to])])
            self.edges[to].append([fr,0,-cost,len(self.edges[fr])-1])
        def MinCost(self,source,sink,flow):
            n=self.n; E=self.edges
            mincost=0
            prev_v=[0]*n; prev_e=[0]*n
            while flow:
                dist=[inf]*n
                dist[source]=0
                q=deque([source])
                Flag=[False] *n
                Flag[source]=True
                while q:
                    v=q.popleft()
                    if not Flag[v] :
                        continue
                    Flag[v]=False
                    for i,(w,cap,cost,_) in enumerate(E[v]):
                        if cap>0 and dist[w]>dist[v]+cost:
                            dist[w]=dist[v]+cost
                            prev_v[w],prev_e[w]=v,i
                            q.append(w)
                            Flag[w]=True
                d,v=flow,sink
                while v!=source:
                    d=min(d,E[prev_v[v]][prev_e[v]][1])
                    v=prev_v[v]
                flow-=d
                mincost+=d*dist[sink]
                v=sink
                while v!=source:
                    e=E[prev_v[v]][prev_e[v]]
                    e[1]-=d
                    E[v][e[3]][1]+=d
                    v=prev_v[v]
            return mincost

    n=int(input())
    flow=MinCostFlow(2*n+6)
    s=0
    for i in range(n):
        rx,ry,rc=map(int,input().split())
        s+=rc
        flow.add_edge(0,i+1,rc,0)
        flow.add_edge(i+1,n+1,inf,-rx-ry)
        flow.add_edge(i+1,n+2,inf,rx-ry)
        flow.add_edge(i+1,n+3,inf,-rx+ry)
        flow.add_edge(i+1,n+4,inf,rx+ry)
    for i in range(n):
        bx,by,bc=map(int,input().split())
        flow.add_edge(n+5+i,2*n+5,bc,0)
        flow.add_edge(n+1,n+5+i,inf,bx+by)
        flow.add_edge(n+2,n+5+i,inf,-bx+by)
        flow.add_edge(n+3,n+5+i,inf,bx-by)
        flow.add_edge(n+4,n+5+i,inf,-bx-by)
    print(-(flow.MinCost(0,2*n+5,s)))

if __name__=='__main__':
    main()