"""3244. Shortest Distance After Road Addition Queries II: permanently bypass vertices under the noncrossing-query contract."""


def solve(n: int, queries: list[list[int]]) -> list[int]:
    """O(n + q) time and O(n + q) space. Inputs are preserved."""
    following = list(range(1, n + 1))
    distance = n - 1
    answer = []
    for left, right in queries:
        if following[left] != -1 and following[left] < right:
            node = following[left]
            while node < right:
                successor = following[node]
                following[node] = -1
                distance -= 1
                node = successor
            following[left] = right
        answer.append(distance)
    return answer


class Solution:
    def shortestDistanceAfterQueries(self, n: int, queries: list[list[int]]) -> list[int]:
        return solve(n, queries)
