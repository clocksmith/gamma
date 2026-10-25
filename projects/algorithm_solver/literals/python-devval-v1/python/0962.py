def solve(values):
    decreasing = []
    for index, value in enumerate(values):
        if not decreasing or value < values[decreasing[-1]]:
            decreasing.append(index)
    widest = 0
    for right in range(len(values) - 1, -1, -1):
        while decreasing and values[decreasing[-1]] <= values[right]:
            widest = max(widest, right - decreasing.pop())
        if not decreasing:
            break
    return widest
