"""255. Verify Preorder Sequence in Binary Search Tree."""
def solve(preorder: list[int]) -> bool:
    lower = float('-inf')
    stack = []
    for value in preorder:
        if value < lower:
            return False
        while stack and value > stack[-1]:
            lower = stack.pop()
        stack.append(value)
    return True

class Solution:
    def verifyPreorder(self, preorder: list[int]) -> bool:
        return solve(preorder)
