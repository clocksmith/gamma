class Node:
    def __init__(self, val=0, left=None, right=None, next=None):
        self.val = val
        self.left = left
        self.right = right
        self.next = next


class Solution:
    def connect(self, root):
        level = root
        while level is not None and level.left is not None:
            current = level
            while current is not None:
                current.left.next = current.right
                current.right.next = current.next.left if current.next is not None else None
                current = current.next
            level = level.left
        return root
