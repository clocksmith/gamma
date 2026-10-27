"""708. Insert into a Sorted Circular Linked List. Insert in place and retain the supplied head even when it is not the minimum node."""

class Node:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def solve(head, insertVal):
    if head is None:
        node = Node(insertVal)
        node.next = node
        return node
    current = head
    while True:
        following = current.next
        if current.val <= insertVal <= following.val:
            break
        if current.val > following.val and (insertVal >= current.val or insertVal <= following.val):
            break
        current = following
        if current is head:
            break
    current.next = Node(insertVal, current.next)
    return head


class Solution:
    def insert(self, head, insertVal):
        return solve(head, insertVal)
