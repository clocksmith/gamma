"""2392. Build a Matrix With Conditions: independent topological coordinates."""


def solve(k: int, rowConditions: list[list[int]], colConditions: list[list[int]]) -> list[list[int]]:
    """O(k^2 + E) time and space, including the returned matrix. Inputs are preserved."""
    def order(conditions):
        adjacency = [[] for _ in range(k + 1)]
        degree = [0] * (k + 1)
        for first, second in conditions:
            adjacency[first].append(second)
            degree[second] += 1
        result = [value for value in range(1, k + 1) if degree[value] == 0]
        head = 0
        while head < len(result):
            value = result[head]
            head += 1
            for following in adjacency[value]:
                degree[following] -= 1
                if degree[following] == 0:
                    result.append(following)
        return result

    rows = order(rowConditions)
    columns = order(colConditions)
    if len(rows) != k or len(columns) != k:
        return []
    column_position = [0] * (k + 1)
    for position, value in enumerate(columns):
        column_position[value] = position
    answer = [[0] * k for _ in range(k)]
    for position, value in enumerate(rows):
        answer[position][column_position[value]] = value
    return answer


class Solution:
    def buildMatrix(self, k: int, rowConditions: list[list[int]], colConditions: list[list[int]]) -> list[list[int]]:
        return solve(k, rowConditions, colConditions)
