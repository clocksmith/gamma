# External ListNode shape: val: int, next: ListNode | None.
class Link:
    def __init__(self, next_node=None):
        self.next = next_node


class Solution:
    def reverseKGroup(self, head, k: int):
        sentinel = Link(head)
        before = sentinel
        while True:
            end = before
            for _ in range(k):
                end = end.next
                if end is None:
                    return sentinel.next

            after = end.next
            first = before.next
            previous = after
            current = first
            while current is not after:
                following = current.next
                current.next = previous
                previous = current
                current = following
            before.next = end
            before = first
