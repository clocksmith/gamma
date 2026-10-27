# Original candidate implementation. Contract: https://leetcode.com/problems/count-nodes-equal-to-average-of-subtree/
def solve(root):
    stack=[(root,False)];data={};answer=0
    while stack:
        node,done=stack.pop()
        if node is None:continue
        if not done:
            stack.append((node,True));stack.append((node.right,False));stack.append((node.left,False))
        else:
            ls,lc=data.get(id(node.left),(0,0));rs,rc=data.get(id(node.right),(0,0))
            total=ls+rs+node.val;count=lc+rc+1;data[id(node)]=(total,count)
            answer+=total//count==node.val
    return answer
