"""Original candidate for LeetCode 2764. Contract: https://leetcode.com/problems/is-array-a-preorder-of-some-binary-tree/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time and space; input describes a valid binary tree as required"""
def solve(nodes):
    stack=[]
    for i,(node,parent) in enumerate(nodes):
        if i==0:
            if parent!=-1:return False
        else:
            while stack and stack[-1]!=parent:stack.pop()
            if not stack:return False
        stack.append(node)
    return True
