"""699. Falling Squares. Compressed half-open coordinates and a range-maximum/range-assignment tree."""

def solve(positions: list[list[int]]) -> list[int]:
    if not positions:
        return []
    coordinates = sorted({x for left, size in positions for x in (left, left + size)})
    rank = {value: i for i, value in enumerate(coordinates)}
    n = len(coordinates) - 1
    maximum, lazy = [0] * (4 * n + 4), [None] * (4 * n + 4)
    def push(node):
        if lazy[node] is not None:
            for child in (node * 2, node * 2 + 1):
                maximum[child] = lazy[node]
                lazy[child] = lazy[node]
            lazy[node] = None
    def query(node, low, high, left, right):
        if left <= low and high <= right:
            return maximum[node]
        push(node)
        middle = (low + high) // 2
        result = 0
        if left <= middle:
            result = query(node * 2, low, middle, left, right)
        if right > middle:
            result = max(result, query(node * 2 + 1, middle + 1, high, left, right))
        return result
    def assign(node, low, high, left, right, value):
        if left <= low and high <= right:
            maximum[node] = lazy[node] = value
            return
        push(node)
        middle = (low + high) // 2
        if left <= middle:
            assign(node * 2, low, middle, left, right, value)
        if right > middle:
            assign(node * 2 + 1, middle + 1, high, left, right, value)
        maximum[node] = max(maximum[node * 2], maximum[node * 2 + 1])
    answer = []
    for left, size in positions:
        a, b = rank[left], rank[left + size] - 1
        height = query(1, 0, n - 1, a, b) + size
        assign(1, 0, n - 1, a, b, height)
        answer.append(maximum[1])
    return answer


class Solution:
    def fallingSquares(self, positions: list[list[int]]) -> list[int]:
        return solve(positions)
