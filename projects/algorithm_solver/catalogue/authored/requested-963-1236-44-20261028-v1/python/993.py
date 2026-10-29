"""Original candidate; no qualification or admission."""

def solve(root,x,y):
    level=[(root,None)]
    while level:
        found={node.val:parent for node,parent in level if node.val in (x,y)}
        if found:return len(found)==2 and found[x] is not found[y]
        level=[(child,node) for node,_ in level for child in (node.left,node.right) if child is not None]
    return False


class Solution:
    def isCousins(self, root, x, y):
        return solve(root, x, y)
