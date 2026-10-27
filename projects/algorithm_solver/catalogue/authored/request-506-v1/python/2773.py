"""Original candidate for LeetCode 2773. Contract: https://leetcode.com/problems/height-of-special-binary-tree/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
solve accepts native special binary-tree nodes (val,left,right), detects circular leaf links by reciprocal identity; JSON compact BFS array input explicitly describes the underlying tree before leaf links.
Complexity: O(n) time and space"""
def build(values):
    if not values or values[0] is None:return []
    nodes=[[values[0],-1,-1]];q=0;p=1
    while q<len(nodes) and p<len(values):
        for side in (1,2):
            if p<len(values) and values[p] is not None:
                nodes[q][side]=len(nodes);nodes.append([values[p],-1,-1])
            p+=1
        q+=1
    return nodes
def solve(root):
    if not isinstance(root,list):
        stack=[(root,0)];answer=0
        while stack:
            node,depth=stack.pop();answer=max(answer,depth)
            if node.left is not None and node.left.right is node:continue
            if node.right is not None and node.right.left is node:continue
            if node.left is not None:stack.append((node.left,depth+1))
            if node.right is not None:stack.append((node.right,depth+1))
        return answer
    # Serialized values describe the underlying tree before leaf links.
    ns=build(root);depth=[0]*len(ns)
    for i,(_,l,r) in enumerate(ns):
        for c in (l,r):
            if c>=0:depth[c]=depth[i]+1
    return max(depth,default=0)
