import sys

sys.setrecursionlimit(100000)

timer = 0

def dfs(current, prev, g, visited, prenum, parent, lowest):
    global timer
    prenum[current] = timer
    lowest[current] = timer
    timer += 1

    visited[current] = True

    for i in range(len(g[current])):
        next_node = g[current][i]
        if not visited[next_node]:
            parent[next_node] = current
            dfs(next_node, current, g, visited, prenum, parent, lowest)
            lowest[current] = min(lowest[current], lowest[next_node])
        elif next_node != prev:
            lowest[current] = min(lowest[current], prenum[next_node])


def art_points(n, g):
    visited = [False] * n
    INFTY = 1 << 20
    prenum = [INFTY] * n
    parent = [INFTY] * n
    parent[0] = -1
    lowest = [INFTY] * n
    global timer
    timer = 1
    dfs(0, -1, g, visited, prenum, parent, lowest)

    ap = set()
    np = 0
    for i in range(1, n):
        p = parent[i]
        if p == 0:
            np += 1
        elif prenum[p] <= lowest[i]:
            ap.add(p)
    if np > 1:
        ap.add(0)
    for line in sorted(ap):
        print(line)


if __name__ == '__main__':
    n, m = [int(v) for v in input().split()]
    g = [[] for i in range(n)]
    for i in range(m):
        s, t = [int(v) for v in input().split()]
        g[s].append(t)
        g[t].append(s)

    art_points(n, g)
