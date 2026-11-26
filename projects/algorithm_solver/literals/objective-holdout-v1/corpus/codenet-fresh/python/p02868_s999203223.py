import heapq
import sys

input = sys.stdin.readline

def dijkstra_heap(s,N,edge):
    d = [float('inf')] * N
    used = [True] * N
    d[s] = 0
    used[s] = False
    edgelist = []
    for a, b in edge[s]:
        heapq.heappush(edgelist, a * (10 ** 6) + b)
    while len(edgelist):
        minedge = heapq.heappop(edgelist)
        if not used[minedge%(10**6)]:
            continue
        v = minedge % (10 ** 6)
        d[v] = minedge // (10 ** 6)
        used[v] = False
        for e in edge[v]:
            if used[e[1]]:
                heapq.heappush(edgelist,(e[0]+d[v])*(10**6)+e[1])
    return d


def main():
    N, M = map(int, input().split())
    edge = [[] for i in range(N)]
    for i in range(N-1):
        edge[i+1].append([0,i])
    for i in range(M):
        L, R, C = map(int, input().split())
        L -= 1
        R -= 1
        edge[L].append([C,R])
        edge[R].append([C,L])
    d = dijkstra_heap(0,N,edge)
    if d[N-1] == float('inf'):
        print(-1)
    else:
        print(d[N-1])
    

if __name__ == "__main__":
    main()