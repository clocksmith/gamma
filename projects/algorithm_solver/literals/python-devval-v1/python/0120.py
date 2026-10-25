def solve(triangle):
    best = [0] * (len(triangle) + 1)
    for row in reversed(triangle):
        for column, value in enumerate(row):
            best[column] = value + min(best[column], best[column + 1])
    return best[0]
