def solve(coords):
    vertical, horizontal = {}, {}
    min_x = min_y = 10**6 + 1
    max_x = max_y = 0
    for x, y in coords:
        min_x, max_x = min(min_x, x), max(max_x, x)
        min_y, max_y = min(min_y, y), max(max_y, y)
        if x not in vertical:
            vertical[x] = [y, y]
        else:
            vertical[x][0] = min(vertical[x][0], y)
            vertical[x][1] = max(vertical[x][1], y)
        if y not in horizontal:
            horizontal[y] = [x, x]
        else:
            horizontal[y][0] = min(horizontal[y][0], x)
            horizontal[y][1] = max(horizontal[y][1], x)
    answer = 0
    for x, (low, high) in vertical.items():
        answer = max(answer, (high - low) * max(x - min_x, max_x - x))
    for y, (low, high) in horizontal.items():
        answer = max(answer, (high - low) * max(y - min_y, max_y - y))
    return answer if answer else -1
