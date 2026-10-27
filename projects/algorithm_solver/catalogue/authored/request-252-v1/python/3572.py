def solve(x, y):
    best = {}
    for key, value in zip(x, y):
        best[key] = max(best.get(key, 0), value)
    if len(best) < 3:
        return -1
    first = second = third = 0
    for value in best.values():
        if value >= first:
            first, second, third = value, first, second
        elif value >= second:
            second, third = value, second
        elif value > third:
            third = value
    return first + second + third
