def solve(root):
    result = []
    frontier = [] if root is None else [root]
    while frontier:
        values = []
        next_frontier = []
        for node in frontier:
            values.append(node.val)
            if node.left is not None:
                next_frontier.append(node.left)
            if node.right is not None:
                next_frontier.append(node.right)
        result.append(values)
        frontier = next_frontier
    return result
