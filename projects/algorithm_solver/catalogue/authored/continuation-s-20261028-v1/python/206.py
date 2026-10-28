class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def reverseList(self, head):
        previous = None
        while head is not None:
            following = head.next
            head.next = previous
            previous = head
            head = following
        return previous
