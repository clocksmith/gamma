"""1632. Rank Transform of a Matrix: equal-value row/column DSUs with deferred rank updates; O(V log V) time and O(V) space, V=rows*columns."""


def solve(matrix: list[list[int]]) -> list[list[int]]:
    rows, columns = len(matrix), len(matrix[0])
    cells = sorted((matrix[row][column], row, column)
                   for row in range(rows) for column in range(columns))
    row_rank = [0] * rows
    column_rank = [0] * columns
    answer = [[0] * columns for _ in range(rows)]
    start = 0
    while start < len(cells):
        end = start + 1
        while end < len(cells) and cells[end][0] == cells[start][0]:
            end += 1
        parent = {}
        weight = {}

        def find(node: int) -> int:
            if node not in parent:
                parent[node] = node
                weight[node] = 1
            while parent[node] != node:
                parent[node] = parent[parent[node]]
                node = parent[node]
            return node

        for index in range(start, end):
            _, row, column = cells[index]
            first, second = find(row), find(rows + column)
            if first != second:
                if weight[first] < weight[second]:
                    first, second = second, first
                parent[second] = first
                weight[first] += weight[second]
        required = {}
        for index in range(start, end):
            _, row, column = cells[index]
            root = find(row)
            required[root] = max(required.get(root, 0), row_rank[row] + 1, column_rank[column] + 1)
        for index in range(start, end):
            _, row, column = cells[index]
            rank = required[find(row)]
            answer[row][column] = rank
            row_rank[row] = max(row_rank[row], rank)
            column_rank[column] = max(column_rank[column], rank)
        start = end
    return answer


class Solution:
    def matrixRankTransform(self, matrix: list[list[int]]) -> list[list[int]]:
        return solve(matrix)
