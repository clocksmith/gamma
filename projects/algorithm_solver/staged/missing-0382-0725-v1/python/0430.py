"""430. Flatten a Multilevel Doubly Linked List. Depth-first in-place relinking preserves every original list node."""

def solve(head):
    if head is None:
        return None
    stack = [head]
    previous = None
    while stack:
        node = stack.pop()
        if node.next:
            stack.append(node.next)
        if node.child:
            stack.append(node.child)
        node.prev = previous
        if previous:
            previous.next = node
        node.child = None
        previous = node
    previous.next = None
    return head


class Solution:
    def flatten(self, head):
        return solve(head)
