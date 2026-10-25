def solve(matrix):
    size = len(matrix)
    previous = [0] * size
    for row in matrix:
        current = []
        for column, value in enumerate(row):
            low = max(0, column - 1)
            high = min(size, column + 2)
            current.append(value + min(previous[low:high]))
        previous = current
    return min(previous)
