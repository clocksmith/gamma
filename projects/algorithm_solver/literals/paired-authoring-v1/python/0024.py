# External ListNode shape: val: int, next: ListNode | None.
class Link:
    def __init__(self, next_node=None):
        self.next = next_node


class Solution:
    def swapPairs(self, head):
        sentinel = Link(head)
        before = sentinel
        while before.next is not None and before.next.next is not None:
            first = before.next
            second = first.next
            first.next = second.next
            second.next = first
            before.next = second
            before = first
        return sentinel.next
