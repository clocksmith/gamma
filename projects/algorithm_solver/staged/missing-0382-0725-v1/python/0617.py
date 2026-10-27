"""617. Merge Two Binary Trees. Merge in place into root1 and graft root2-only subtrees; those grafted nodes remain shared."""

def solve(root1, root2):
    if root1 is None:
        return root2
    if root2 is None:
        return root1
    stack = [(root1, root2)]
    while stack:
        a, b = stack.pop()
        a.val += b.val
        if a.left and b.left:
            stack.append((a.left, b.left))
        elif a.left is None:
            a.left = b.left
        if a.right and b.right:
            stack.append((a.right, b.right))
        elif a.right is None:
            a.right = b.right
    return root1


class Solution:
    def mergeTrees(self, root1, root2):
        return solve(root1, root2)
