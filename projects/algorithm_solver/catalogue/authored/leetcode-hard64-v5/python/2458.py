"""2458. Height of Binary Tree After Subtree Removal Queries. Exclude contiguous preorder subtree intervals using prefix and suffix depth maxima."""


def solve(root, queries: list[int]) -> list[int]:
    """O(n+q) time and O(n) auxiliary space. Inputs are preserved."""
    entry = {}
    leave = {}
    depths = []
    stack = [(root, 0, False)]
    while stack:
        node, depth, exiting = stack.pop()
        if exiting:
            leave[node.val] = len(depths)
            continue
        entry[node.val] = len(depths)
        depths.append(depth)
        stack.append((node, depth, True))
        if node.right is not None:
            stack.append((node.right, depth + 1, False))
        if node.left is not None:
            stack.append((node.left, depth + 1, False))
    size = len(depths)
    prefix = [-1] * (size + 1)
    suffix = [-1] * (size + 1)
    for index in range(size):
        prefix[index + 1] = max(prefix[index], depths[index])
    for index in range(size - 1, -1, -1):
        suffix[index] = max(suffix[index + 1], depths[index])
    return [max(prefix[entry[value]], suffix[leave[value]]) for value in queries]


class Solution:
    def treeQueries(self, root, queries: list[int]) -> list[int]:
        return solve(root, queries)
