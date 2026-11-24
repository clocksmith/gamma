import sys
from collections import deque


def bfs(links, s, limit):
    not_reachable = [True] * len(links)
    q = deque([(0, s, -1)])
    while q:
        cost, v, p = q.popleft()
        if cost > limit:
            break
        not_reachable[v] = False
        cost += 1
        q.extend((cost, u, v) for u in links[v] if u != p)
    return not_reachable


def solve(n, k, ab):
    if k == 1:
        return n - 2

    links = [set() for _ in range(n)]
    for a, b in zip(ab[0::2], ab[1::2]):
        a -= 1
        b -= 1
        links[a].add(b)
        links[b].add(a)

    ans = n
    thr = k // 2
    if k % 2 == 0:
        ans = min(sum(bfs(links, v, thr)) for v in range(n))
    else:
        dists = [bfs(links, v, thr) for v in range(n)]
        for a, b in zip(ab[0::2], ab[1::2]):
            a -= 1
            b -= 1
            ans = min(ans, sum(d1 and d2 for d1, d2 in zip(dists[a], dists[b])))
    return ans


n, k, *ab = map(int, sys.stdin.buffer.read().split())
print(solve(n, k, ab))
