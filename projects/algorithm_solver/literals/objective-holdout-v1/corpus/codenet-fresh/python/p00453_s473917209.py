from heapq import heappop, heappush

while True:
    n, m = map(int, input().split())
    if not n:
        break

    num_stones = 0
    row_stones = [None] * n
    edges = [None] * n
    visited = [None] * n
    for row in range(n):
        (num, *stones) = map(int, input().split())
        row_stones[row] = list(zip(*[iter(stones)] * 2))
        edges[row] = [None] * num
        visited[row] = [1] * num

    for row, stones in enumerate(row_stones):
        next_stones = [row_stones[row + j] if row + j < n else [] for j in (1, 2)]
        for i, (column1, slip1) in enumerate(stones):
            edges[row][i] = [{(abs(column1 - column2) * (slip1 + slip2), j)
                              for j, (column2, slip2) in enumerate(next_stones[k])} for k in (0, 1)]

    queue = [(0, 0, -m, i) for i in range(len(row_stones[0]))]
    if m:
        queue.extend((0, -1, -m + 1, i) for i in range(len(row_stones[1])))

    while queue:
        total_risk, row, remains, i = heappop(queue)
        row = -row
        if row == n - 1 or (remains and row == n - 2):
            print(total_risk)
            break
        if visited[row][i] <= remains:
            continue
        visited[row][i] = remains
        next_stones = edges[row][i]
        for risk, j in next_stones[0]:
            heappush(queue, (total_risk + risk, -row - 1, remains, j))
        if remains:
            for risk, j in next_stones[1]:
                heappush(queue, (total_risk + risk, -row - 2, remains + 1, j))