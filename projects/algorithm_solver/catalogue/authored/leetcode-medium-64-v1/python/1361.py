"""1361. Validate Binary Tree Nodes: require unique parents and one root that reaches every node."""


def solve(n: int, leftChild: list[int], rightChild: list[int]) -> bool:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    indegree = [0] * n
    for children in (leftChild, rightChild):
        for child in children:
            if child != -1:
                indegree[child] += 1
                if indegree[child] > 1:
                    return False
    roots = [node for node, degree in enumerate(indegree) if degree == 0]
    if len(roots) != 1:
        return False
    seen = [False] * n
    stack = [roots[0]]
    visited = 0
    while stack:
        node = stack.pop()
        if seen[node]:
            return False
        seen[node] = True
        visited += 1
        for child in (leftChild[node], rightChild[node]):
            if child != -1:
                stack.append(child)
    return visited == n


class Solution:
    def validateBinaryTreeNodes(self, n: int, leftChild: list[int], rightChild: list[int]) -> bool:
        return solve(n, leftChild, rightChild)
