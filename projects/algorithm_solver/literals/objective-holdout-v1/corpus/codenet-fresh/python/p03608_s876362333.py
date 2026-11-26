import itertools
def main():

    N, M, R = map(int, input().split())
    r = list(map(int, input().split()))
    r = [v-1 for v in r]

    dist = [[float('inf') for _ in range(N)] for _ in range(N)]
    for i in range(N): dist[i][i] = 0
    for _ in range(M):
        a, b, c = map(int, input().split())
        dist[a-1][b-1] = c
        dist[b-1][a-1] = c

    for k in range(N):
        for i in range(N):
            for j in range(N):
                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])

    path = itertools.permutations(r)
    ans = float('inf')
    for p in path:
        d = 0
        for i in range(len(p)-1):
            d += dist[p[i]][p[i+1]]
        ans = min(ans, d)

    return ans

if __name__ == '__main__':
    print(main())