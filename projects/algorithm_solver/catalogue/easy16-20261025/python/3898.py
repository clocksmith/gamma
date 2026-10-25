def solve(matrix: list[list[int]]) -> list[int]:
    """Sum incident edges per vertex. O(n^2) time, O(n) output space."""
    answer = []
    for row in matrix:
        degree = 0
        for edge in row:
            degree += edge
        answer.append(degree)
    return answer
