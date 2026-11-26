import sys
sys.setrecursionlimit(10000000)
MOD = 10 ** 9 + 7
INF = 10 ** 15

def main():
    N = int(input())
    M = int(input())
    dist = [[INF]*N for _ in range(N)]
    for _ in range(M):
        a,b,c,d = map(int,input().split(','))
        a -= 1
        b -= 1
        dist[a][b] = c
        dist[b][a] = d
    s,g,v,p = map(int,input().split(','))
    for k in range(N):
        for i in range(N):
            for j in range(N):
                dist[i][j] = min(dist[i][k] + dist[k][j],dist[i][j])
    s -= 1
    g -= 1
    ans = v - dist[s][g] - dist[g][s] - p
    print(ans)
if __name__ == '__main__':
    main()
