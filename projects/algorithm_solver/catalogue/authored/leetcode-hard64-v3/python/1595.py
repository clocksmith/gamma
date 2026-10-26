"""1595. Minimum Cost to Connect Two Groups of Points: one edge per first-group point, then cheapest uncovered columns; O(rows*columns*2^columns) time."""


def solve(cost: list[list[int]]) -> int:
    columns = len(cost[0])
    full = 1 << columns
    cheapest = [min(row[column] for row in cost) for column in range(columns)]
    previous = [float('inf')] * full
    previous[0] = 0
    for row in cost:
        current = [float('inf')] * full
        for mask, total in enumerate(previous):
            if total == float('inf'):
                continue
            for column, price in enumerate(row):
                following = mask | (1 << column)
                current[following] = min(current[following], total + price)
        previous = current
    answer = float('inf')
    for mask, total in enumerate(previous):
        for column in range(columns):
            if not mask & (1 << column):
                total += cheapest[column]
        answer = min(answer, total)
    return answer


class Solution:
    def connectTwoGroups(self, cost: list[list[int]]) -> int:
        return solve(cost)
