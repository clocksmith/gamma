while True:
    n = int(input())
    if n == 0:break
    edges = [[] for _ in range(n)]
    for _ in range(n - 1):
        a, b, t = map(int, input().split())
        a -= 1
        b -= 1
        edges[a].append([b, t])
        edges[b].append([a, t])
    used = [False] * n
    is_leaf = [False] * n
    for i in range(1, n):
        if len(edges[i]) == 1:is_leaf[i] = True


    def check(x):
        used[x] = True
        times = [0]
        max_path = 0
        for to, t in edges[x]:
            if not used[to] and not is_leaf[to]:
                time, path = check(to)
                times.append(time + t * 2)
                max_path = max(max_path, path + t)
        return sum(times), max_path


    total_time, max_path = check(0)
    print(total_time - max_path)
