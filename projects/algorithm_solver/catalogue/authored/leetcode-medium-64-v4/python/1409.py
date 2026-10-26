"""1409. Queries on a Permutation With Key: reserve front positions and maintain occupied ranks in a Fenwick tree."""


def solve(queries: list[int], m: int) -> list[int]:
    """O((m + q) log(m + q + 1)) time and O(m + q) auxiliary space; inputs are read-only."""
    count = len(queries)
    tree = [0] * (m + count + 1)
    positions = [0] * (m + 1)

    def update(index: int, delta: int) -> None:
        while index < len(tree):
            tree[index] += delta
            index += index & -index

    def prefix(index: int) -> int:
        total = 0
        while index:
            total += tree[index]
            index -= index & -index
        return total

    for value in range(1, m + 1):
        positions[value] = count + value
        update(positions[value], 1)
    front = count
    result = []
    for value in queries:
        result.append(prefix(positions[value] - 1))
        update(positions[value], -1)
        positions[value] = front
        update(front, 1)
        front -= 1
    return result


class Solution:
    def processQueries(self, queries: list[int], m: int) -> list[int]:
        return solve(queries, m)
