"""Original frontend 255 variant; qualification unknown."""


def solve(preorder) -> bool:
    stack = []
    low = -(10**18)
    for x in preorder:
        if x < low:
            return False
        while stack and stack[-1] < x:
            low = stack.pop()
        stack.append(x)
    return True


verifyPreorder = solve


class Solution:
    def verifyPreorder(self, preorder) -> bool:
        return solve(preorder)
