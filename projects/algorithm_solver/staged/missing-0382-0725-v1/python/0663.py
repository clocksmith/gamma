"""663. Equal Tree Partition."""

def solve(root):
    if root is None:
        return False
    sums = {}
    proper = set()
    stack = [(root, False)]
    while stack:
        node, ready = stack.pop()
        if not ready:
            stack.append((node, True))
            if node.right:
                stack.append((node.right, False))
            if node.left:
                stack.append((node.left, False))
        else:
            total = node.val + sums.get(id(node.left), 0) + sums.get(id(node.right), 0)
            sums[id(node)] = total
            if node is not root:
                proper.add(total)
    total = sums[id(root)]
    return total % 2 == 0 and total // 2 in proper


class Solution:
    def checkEqualTree(self, root):
        return solve(root)
