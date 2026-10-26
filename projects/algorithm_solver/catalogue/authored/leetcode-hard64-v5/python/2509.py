"""2509. Cycle Length Queries in a Tree. Climb larger heap labels to their lowest common ancestor."""


def solve(n: int, queries: list[list[int]]) -> list[int]:
    """O(q*n) time and O(1) auxiliary space excluding output. Inputs are preserved."""
    answer = []
    for first, second in queries:
        length = 1
        while first != second:
            if first > second:
                first //= 2
            else:
                second //= 2
            length += 1
        answer.append(length)
    return answer


class Solution:
    def cycleLengthQueries(self, n: int, queries: list[list[int]]) -> list[int]:
        return solve(n, queries)
