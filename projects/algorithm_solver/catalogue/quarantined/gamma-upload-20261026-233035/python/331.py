"""331. Verify Preorder Serialization of a Binary Tree."""
def solve(preorder: str) -> bool:
    slots = 1
    for token in preorder.split(','):
        slots -= 1
        if slots < 0:
            return False
        if token != '#':
            slots += 2
    return slots == 0

class Solution:
    def isValidSerialization(self, preorder: str) -> bool:
        return solve(preorder)
