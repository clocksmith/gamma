class Solution:
    def totalNQueens(self, n: int) -> int:
        columns = [False] * n
        descending = [False] * (2 * n + 1)
        ascending = [False] * (2 * n + 1)

        def count_from(row: int) -> int:
            if row == n:
                return 1
            total = 0
            for column in range(n):
                down = row - column + n
                up = row + column
                if columns[column] or descending[down] or ascending[up]:
                    continue
                columns[column] = True
                descending[down] = True
                ascending[up] = True
                total += count_from(row + 1)
                columns[column] = False
                descending[down] = False
                ascending[up] = False
            return total

        return count_from(0)
