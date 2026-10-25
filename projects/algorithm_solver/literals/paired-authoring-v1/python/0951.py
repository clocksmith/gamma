# External nodes have val, left and right; absent children are None.
def canonical_tree(root, intern: dict) -> int:
    if root is None:
        return 0
    labels = {}
    stack = [(root, False)]
    while stack:
        node, expanded = stack.pop()
        if not expanded:
            stack.append((node, True))
            if node.right is not None:
                stack.append((node.right, False))
            if node.left is not None:
                stack.append((node.left, False))
        else:
            left = 0 if node.left is None else labels[id(node.left)]
            right = 0 if node.right is None else labels[id(node.right)]
            key = (node.val, min(left, right), max(left, right))
            if key not in intern:
                intern[key] = len(intern) + 1
            labels[id(node)] = intern[key]
    return labels[id(root)]


class Solution:
    def flipEquiv(self, root1: "TreeNode | None", root2: "TreeNode | None") -> bool:
        intern = {}
        return canonical_tree(root1, intern) == canonical_tree(root2, intern)
