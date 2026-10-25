def change_count(counts: dict, key: int, delta: int) -> None:
    updated = counts.get(key, 0) + delta
    if updated == 0:
        counts.pop(key, None)
    else:
        counts[key] = updated


class Solution:
    def gridIllumination(self, n: int, lamps: list[list[int]], queries: list[list[int]]) -> list[int]:
        active = set()
        rows = {}
        columns = {}
        descending = {}
        ascending = {}
        for row, column in lamps:
            if (row, column) in active:
                continue
            active.add((row, column))
            change_count(rows, row, 1)
            change_count(columns, column, 1)
            change_count(descending, row - column, 1)
            change_count(ascending, row + column, 1)
        output = []
        for row, column in queries:
            illuminated = rows.get(row, 0) > 0 or columns.get(column, 0) > 0
            illuminated = illuminated or descending.get(row - column, 0) > 0
            illuminated = illuminated or ascending.get(row + column, 0) > 0
            output.append(1 if illuminated else 0)
            for next_row in range(row - 1, row + 2):
                for next_column in range(column - 1, column + 2):
                    if 0 <= next_row < n and 0 <= next_column < n:
                        if (next_row, next_column) in active:
                            active.remove((next_row, next_column))
                            change_count(rows, next_row, -1)
                            change_count(columns, next_column, -1)
                            change_count(descending, next_row - next_column, -1)
                            change_count(ascending, next_row + next_column, -1)
        return output
