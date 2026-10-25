# External ListNode shape: val: int, next: ListNode | None.
class Link:
    def __init__(self, next_node=None):
        self.next = next_node


class Solution:
    def deleteDuplicates(self, head):
        sentinel = Link(head)
        before = sentinel
        current = head
        while current is not None:
            after = current.next
            while after is not None and after.val == current.val:
                after = after.next
            if current.next is after:
                before = current
            else:
                before.next = after
            current = after
        return sentinel.next
