def solve(n, buildings):
    rows, columns = {}, {}
    for x, y in buildings:
        low, high = rows.get(x, (y, y))
        rows[x] = (min(low, y), max(high, y))
        low, high = columns.get(y, (x, x))
        columns[y] = (min(low, x), max(high, x))
    return sum(rows[x][0] < y < rows[x][1] and columns[y][0] < x < columns[y][1]
               for x, y in buildings)
