INF = 10000000

def bf(es, dist, c, s, d):
    dist[s][0] = 0

    isUpdated = True
    while isUpdated:
        isUpdated = False
        for e in es:
            a, b, f = e
            for i in range(c+1):
                if dist[a][i] != INF and dist[a][i] + f < dist[b][i]:
                    dist[b][i] = dist[a][i] + f
                    isUpdated = True
                if dist[a][i] != INF and (i+1) <= c and dist[a][i] + f / 2 < dist[b][i+1]:
                    dist[b][i+1] = dist[a][i] + int(f / 2)
                    isUpdated = True
    
    return min(dist[d])

if __name__ == '__main__':
    while True:
        c, n, m, s, d = map(int, input().split())
        if c == 0:
            break

        s -= 1
        d -= 1
        es = []
        dist = [[INF for _ in range(c+1)] for __ in range(n)] # dist[i][j]: ???i?????§????????????j????????£??????????????????
        for _ in range(m):
            a, b, f = map(int, input().split())
            a -= 1
            b -= 1
            es.append([a, b, f])
            es.append([b, a, f])

        print(bf(es, dist, c, s, d))