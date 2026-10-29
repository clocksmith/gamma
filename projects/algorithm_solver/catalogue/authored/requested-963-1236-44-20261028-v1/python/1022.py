"""Original candidate; no qualification or admission."""

def solve(root):
    stack=[(root,0)];answer=0
    while stack:
        node,value=stack.pop();value=value*2+node.val
        if node.left is None and node.right is None:answer+=value
        if node.left is not None:stack.append((node.left,value))
        if node.right is not None:stack.append((node.right,value))
    return answer


class Solution:
    def sumRootToLeaf(self, root):
        return solve(root)
