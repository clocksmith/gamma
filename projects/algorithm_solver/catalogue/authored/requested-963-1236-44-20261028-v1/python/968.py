"""Original candidate; no qualification or admission."""

def solve(root):
    state={};count=0;stack=[(root,False)]
    while stack:
        node,visited=stack.pop()
        if node is None:continue
        if not visited:stack.extend([(node,True),(node.left,False),(node.right,False)]);continue
        left=state.get(id(node.left),1);right=state.get(id(node.right),1)
        if left==0 or right==0:state[id(node)]=2;count+=1
        else:state[id(node)]=1 if left==2 or right==2 else 0
    return count+(state[id(root)]==0)


class Solution:
    def minCameraCover(self, root):
        return solve(root)
