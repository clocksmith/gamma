"""Original candidate; no qualification or admission."""

def solve(root):
    records=[];stack=[(root,0,0)]
    while stack:
        node,row,col=stack.pop();records.append((col,row,node.val))
        if node.left is not None:stack.append((node.left,row+1,col-1))
        if node.right is not None:stack.append((node.right,row+1,col+1))
    out=[];previous=None
    for col,_,value in sorted(records):
        if col!=previous:out.append([]);previous=col
        out[-1].append(value)
    return out


class Solution:
    def verticalTraversal(self, root):
        return solve(root)
