# External ListNode shape: val: int, next: ListNode | None.
class Link:
    def __init__(self, next_node=None):
        self.next = next_node


class Solution:
    def partition(self, head, x):
        lower_sentinel = Link()
        upper_sentinel = Link()
        lower_tail = lower_sentinel
        upper_tail = upper_sentinel
        current = head
        while current is not None:
            next_node = current.next
            current.next = None
            if current.val < x:
                lower_tail.next = current
                lower_tail = current
            else:
                upper_tail.next = current
                upper_tail = current
            current = next_node

        lower_tail.next = upper_sentinel.next
        return lower_sentinel.next
