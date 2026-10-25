def solve(stones):
    parents = list(range(len(stones)))
    sizes = [1] * len(stones)

    def find(node):
        while node != parents[node]:
            parents[node] = parents[parents[node]]
            node = parents[node]
        return node

    def connect(first, second):
        first, second = find(first), find(second)
        if first == second:
            return 0
        if sizes[first] < sizes[second]:
            first, second = second, first
        parents[second] = first
        sizes[first] += sizes[second]
        return 1

    rows = {}
    columns = {}
    removed = 0
    for index, (row, column) in enumerate(stones):
        if row in rows:
            removed += connect(index, rows[row])
        else:
            rows[row] = index
        if column in columns:
            removed += connect(index, columns[column])
        else:
            columns[column] = index
    return removed
