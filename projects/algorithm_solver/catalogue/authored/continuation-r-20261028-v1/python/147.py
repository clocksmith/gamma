class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def insertionSortList(self, head):
        if head is None:
            return None
        dummy = ListNode(0, head)
        last_sorted = head
        current = head.next
        while current is not None:
            if last_sorted.val <= current.val:
                last_sorted = current
            else:
                previous = dummy
                while previous.next.val <= current.val:
                    previous = previous.next
                last_sorted.next = current.next
                current.next = previous.next
                previous.next = current
            current = last_sorted.next
        return dummy.next
