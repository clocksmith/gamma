"""2076. Process Restricted Friend Requests."""


def solve(n: int, restrictions: list[list[int]], requests: list[list[int]]) -> list[bool]:
    """Union-find with pre-merge restriction checks; O((n+R*Q)*alpha(n)) time, O(n+Q) space. Inputs are preserved."""
    parent = list(range(n))
    sizes = [1] * n

    def find(node):
        while node != parent[node]:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    answer = []
    for first, second in requests:
        left, right = find(first), find(second)
        allowed = True
        if left != right:
            for banned_first, banned_second in restrictions:
                a, b = find(banned_first), find(banned_second)
                if (a == left and b == right) or (a == right and b == left):
                    allowed = False
                    break
            if allowed:
                if sizes[left] < sizes[right]:
                    left, right = right, left
                parent[right] = left
                sizes[left] += sizes[right]
        answer.append(allowed)
    return answer


class Solution:
    def friendRequests(self, n: int, restrictions: list[list[int]], requests: list[list[int]]) -> list[bool]:
        return solve(n, restrictions, requests)
