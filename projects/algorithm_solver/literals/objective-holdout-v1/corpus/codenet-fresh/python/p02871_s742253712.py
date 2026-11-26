def warshall_floid(graph):
    """warshall-floid法: 各頂点から各頂点への最短距離を求める
    重み付きグラフgraphは隣接リストで与えられる
    計算量: O(|N|^3)
    """
    n = len(graph)
    INF = 10**18
    dp = [[INF]*n for i in range(n)]
    for i in range(n):
        dp[i][i] = 0

    for i in range(n):
        for j, cost in graph[i]:
            dp[i][j] = cost
            dp[j][i] = cost

    for k in range(n):
        for i in range(n):
            for j in range(n):
                dp[i][j] = min(dp[i][j], dp[i][k] + dp[k][j])
    return dp


def trace_route(start, goal):
    """warshall-floid法で求めた最短距離を通るための経路を復元する
    計算量: O(|N|^2)
    """
    pos = start
    ans = []
    while pos != goal:
        ans.append(pos)
        for next_pos in range(n):
            if next_pos != pos and dp[pos][next_pos] + dp[next_pos][goal] == dp[pos][goal]:
                pos = next_pos
                break
    ans.append(goal)
    return ans


# 値を入力する
n, m = map(int, input().split())
info = [list(map(int, input().split())) for i in range(m)]
t_max = int(input())
query = [None] * t_max
for i in range(t_max):
    tmp = int(input())
    query[i] = [list(map(int, input().split())) for i in range(tmp)]

# グラフを構築
graph = [[] for i in range(n)]
for a, b, cost in info:
    a -= 1
    b -= 1
    graph[a].append((b, cost))
    graph[b].append((a, cost))

# 最短距離を求める
dp = warshall_floid(graph)

visited = [False] * n
visited[0] = True
route = [0]
pos = 0
total_cost = 0
while True:
    kyori = 10**9
    next_pos = -1
    for next_p, cost in enumerate(dp[pos]):
        if visited[next_p]:
            continue
        if cost< kyori:
            kyori = cost
            next_pos = next_p
    if next_pos == -1:
        break
    else:
        visited[next_pos] = True
        route.append(next_pos)
        total_cost += kyori

for i in range(n-1):
    pos = route[i]
    next_pos = route[i+1]

for i in range(t_max):
	print(-1)