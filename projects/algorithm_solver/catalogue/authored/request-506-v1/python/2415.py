# Original candidate implementation. Contract: https://leetcode.com/problems/reverse-odd-levels-of-binary-tree/
def solve(root):
    level=[root];depth=0
    while level:
        if depth%2:
            for i in range(len(level)//2):level[i].val,level[-1-i].val=level[-1-i].val,level[i].val
        level=[child for node in level for child in (node.left,node.right) if child is not None];depth+=1
    return root
