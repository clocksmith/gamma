class Node:
    def __init__(self, val=0, left=None, right=None, next=None):
        self.val = val
        self.left = left
        self.right = right
        self.next = next


class Solution:
    def connect(self, root):
        level = root
        while level is not None:
            head = tail = None
            current = level
            while current is not None:
                for child in (current.left, current.right):
                    if child is not None:
                        if tail is None:
                            head = child
                        else:
                            tail.next = child
                        tail = child
                current = current.next
            if tail is not None:
                tail.next = None
            level = head
        return root
