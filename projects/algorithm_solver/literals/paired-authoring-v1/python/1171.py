# External nodes have val and next; absent next is None.
class Link:
    def __init__(self, next_node=None):
        self.next = next_node


class Solution:
    def removeZeroSumSublists(self, head):
        sentinel = Link(head)
        last = {0: sentinel}
        total = 0
        current = head
        while current is not None:
            total += current.val
            last[total] = current
            current = current.next
        current = sentinel
        total = 0
        while current is not None:
            current.next = last[total].next
            current = current.next
            if current is not None:
                total += current.val
        return sentinel.next
