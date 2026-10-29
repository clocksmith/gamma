"""Original frontend 1214 variant; qualification unknown."""


def _collect(root):
    if isinstance(root, list):
        return {x for x in root if x is not None}
    vals = set()
    stack = [root]
    while stack:
        node = stack.pop()
        if node is not None:
            vals.add(node.val)
            stack.append(node.left)
            stack.append(node.right)
    return vals


def solve(root1, root2, target: int) -> bool:
    s1 = _collect(root1)
    s2 = _collect(root2)
    return any((target - y) in s1 for y in s2)


twoSumBSTs = solve


class Solution:
    def twoSumBSTs(self, root1, root2, target: int) -> bool:
        return solve(root1, root2, target)
